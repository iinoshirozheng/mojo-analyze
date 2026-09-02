# Disclosed CPU/GPU split, same spirit as the other *_gpu.mojo files in this
# repo. Unlike word-frequency's ~unbounded vocabulary, CSV category
# cardinality is small and fixed (99 in the real data) -- that makes this
# the most naturally GPU-friendly of the three non-Mandelbrot categories:
# CPU parses the CSV once, assigning each row's category a small integer id
# (0..~98, via the same byte-span technique csvagg.mojo/wordfreq_gpu.mojo
# use) and computing quantity*price_cents per row -- both cheap, mostly
# sequential byte-scanning work. The GPU's job is a genuine, clean, fully
# parallel reduction: one thread per row, atomicAdd(revenue[category_id],
# row_revenue) into a small fixed-size accumulator array -- no hash-table
# collision handling needed on the GPU side at all, since ids are already
# small dense integers. TIME_SECONDS covers the whole pipeline (file read
# through final lookup), matching every other category's convention, so
# this is directly comparable to the CPU-only csvagg.mojo's ~0.65s.
#
# SECOND hardware limitation found (first was Mandelbrot's missing Metal
# float64): Apple GPU also has no atomic add for 64-bit integers -- confirmed
# empirically ("Atomic operation is not supported for this type on Apple
# GPU" at compile time for Int64). A single row's revenue fits comfortably
# in 32 bits (max ~20 * 500,000 = 10,000,000), but the *summed* revenue for
# a busy category across up to 10M rows can exceed the 32-bit range, so a
# 32-bit atomic accumulator alone isn't enough either. Fix: split each
# category's running sum into two UInt32 atomics (sums_lo, sums_hi) and use
# the standard lock-free carry-propagation trick -- fetch_add on sums_lo
# returns the pre-addition value; if that value is large enough that adding
# this row's revenue would have wrapped past 2^32, this thread atomically
# bumps sums_hi by one carry. This is linearizable per-thread (each thread
# only needs to know whether *its own* addition crossed the boundary) and
# reconstructs the exact Int64 sum on the host as `(hi << 32) + lo`.
from std.sys import argv
from std.sys.info import has_accelerator
from std.time import perf_counter_ns
from std.math import ceildiv
from std.gpu import global_idx
from max.gpu.host import DeviceContext
from std.atomic import Atomic
from layout import TileTensor, TensorLayout, row_major

comptime CAT_CAPACITY = 1024
comptime CAT_MASK = CAT_CAPACITY - 1
comptime BLOCK = 256
comptime FNV_OFFSET: UInt64 = 14695981039346656037
comptime FNV_PRIME: UInt64 = 1099511628211
comptime COMMA: UInt8 = 44
comptime DIGIT_0: UInt8 = 48


def parse_csv_arg() -> String:
    var args = argv()
    var i = 1
    while i < len(args):
        if String(args[i]) == "--csv" and i + 1 < len(args):
            return String(args[i + 1])
        i += 1
    return "benchmarks/csvagg/data/orders.csv"


def revenue_kernel[
    CIT: TensorLayout, RT: TensorLayout, ST: TensorLayout
](
    cat_ids: TileTensor[DType.int32, CIT, MutAnyOrigin],
    row_revenue: TileTensor[DType.int32, RT, MutAnyOrigin],
    sums_lo: TileTensor[DType.uint32, ST, MutAnyOrigin],
    sums_hi: TileTensor[DType.uint32, ST, MutAnyOrigin],
    total_rows: Int32,
):
    comptime assert cat_ids.flat_rank == 1, "expected 1D cat_ids"
    comptime assert row_revenue.flat_rank == 1, "expected 1D row_revenue"
    comptime assert sums_lo.flat_rank == 1, "expected 1D sums_lo"
    var idx = global_idx.x
    if idx < Int(total_rows):
        var cid = rebind[Int32](cat_ids[Int(idx)])
        var rev = UInt32(rebind[Int32](row_revenue[Int(idx)]))
        # Same disclosed pointer-arithmetic deprecation as wordfreq_gpu.mojo:
        # no non-deprecated way yet to form an offset pointer for Atomic ops.
        var old_lo = Atomic.fetch_add(sums_lo.ptr + Int(cid), rev)
        if old_lo > (UInt32(4294967295) - rev):
            _ = Atomic.fetch_add(sums_hi.ptr + Int(cid), UInt32(1))


def main() raises:
    comptime assert has_accelerator(), "Requires a GPU"

    var csv_path = parse_csv_arg()

    var start = perf_counter_ns()

    var text = open(csv_path, "r").read()
    var data = text.as_bytes()
    var n = len(data)

    var slot_used = List[Bool](length=CAT_CAPACITY, fill=False)
    var slot_hash = List[UInt64](length=CAT_CAPACITY, fill=0)
    var slot_start = List[Int](length=CAT_CAPACITY, fill=0)
    var slot_end = List[Int](length=CAT_CAPACITY, fill=0)
    var cat_ids = List[Int32]()
    var row_revenue = List[Int32]()

    var i = 0
    while i < n and data[i] != 10:
        i += 1
    i += 1

    while i < n:
        while i < n and data[i] != COMMA:
            i += 1
        i += 1

        var cat_start = i
        while i < n and data[i] != COMMA:
            i += 1
        var cat_end = i
        i += 1

        var quantity = 0
        while i < n and data[i] != COMMA:
            quantity = quantity * 10 + Int(data[i] - DIGIT_0)
            i += 1
        i += 1

        var price_cents = 0
        while i < n and data[i] != COMMA and data[i] != 10:
            price_cents = price_cents * 10 + Int(data[i] - DIGIT_0)
            i += 1
        while i < n and data[i] != 10:
            i += 1
        i += 1

        var span_len = cat_end - cat_start
        var h: UInt64 = FNV_OFFSET
        var k = cat_start
        while k < cat_end:
            h = h ^ UInt64(data[k])
            h = h * FNV_PRIME
            k += 1

        var slot = Int(h) & CAT_MASK
        while True:
            if not slot_used[slot]:
                slot_used[slot] = True
                slot_hash[slot] = h
                slot_start[slot] = cat_start
                slot_end[slot] = cat_end
                break
            var matches = False
            if slot_hash[slot] == h and (slot_end[slot] - slot_start[slot]) == span_len:
                matches = True
                var j = 0
                while j < span_len:
                    if data[slot_start[slot] + j] != data[cat_start + j]:
                        matches = False
                        break
                    j += 1
            if matches:
                break
            slot = (slot + 1) & CAT_MASK

        cat_ids.append(Int32(slot))
        row_revenue.append(Int32(quantity * price_cents))

    var total_rows = len(cat_ids)

    var ctx = DeviceContext()
    var ids_buf = ctx.enqueue_create_buffer[DType.int32](total_rows)
    var rev_buf = ctx.enqueue_create_buffer[DType.int32](total_rows)
    with ids_buf.map_to_host() as ids_mapped:
        var ids_view = TileTensor(ids_mapped, row_major(total_rows))
        for idx2 in range(total_rows):
            ids_view[idx2] = cat_ids[idx2]
    with rev_buf.map_to_host() as rev_mapped:
        var rev_view = TileTensor(rev_mapped, row_major(total_rows))
        for idx2 in range(total_rows):
            rev_view[idx2] = row_revenue[idx2]

    var sums_lo_buf = ctx.enqueue_create_buffer[DType.uint32](CAT_CAPACITY)
    var sums_hi_buf = ctx.enqueue_create_buffer[DType.uint32](CAT_CAPACITY)
    sums_lo_buf.enqueue_fill(0)
    sums_hi_buf.enqueue_fill(0)

    var ids_layout = row_major(total_rows)
    var rev_layout = row_major(total_rows)
    var sums_layout = row_major(CAT_CAPACITY)
    var ids_t = TileTensor(ids_buf, ids_layout)
    var rev_t = TileTensor(rev_buf, rev_layout)
    var sums_lo_t = TileTensor(sums_lo_buf, sums_layout)
    var sums_hi_t = TileTensor(sums_hi_buf, sums_layout)

    comptime kernel = revenue_kernel[type_of(ids_layout), type_of(rev_layout), type_of(sums_layout)]
    ctx.enqueue_function[kernel](
        ids_t, rev_t, sums_lo_t, sums_hi_t, Int32(total_rows),
        grid_dim=ceildiv(total_rows, BLOCK),
        block_dim=BLOCK,
    )

    var unique_categories = 0
    var top_category = ""
    var top_revenue = Int64(-1)
    var have_top = False
    with sums_lo_buf.map_to_host() as lo_mapped:
        with sums_hi_buf.map_to_host() as hi_mapped:
            var host_lo = TileTensor(lo_mapped, sums_layout)
            var host_hi = TileTensor(hi_mapped, sums_layout)
            var s = 0
            while s < CAT_CAPACITY:
                if slot_used[s]:
                    unique_categories += 1
                    var rev = (Int64(UInt64(host_hi[s])) << 32) + Int64(UInt64(host_lo[s]))
                    var buf = List[UInt8]()
                    var p = slot_start[s]
                    while p < slot_end[s]:
                        buf.append(data[p])
                        p += 1
                    var category = String(unsafe_from_utf8=Span(buf))
                    if not have_top or rev > top_revenue or (rev == top_revenue and category < top_category):
                        top_category = category
                        top_revenue = rev
                        have_top = True
                s += 1

    var elapsed_ns = perf_counter_ns() - start
    var elapsed = Float64(elapsed_ns) / 1_000_000_000.0

    print("TIME_SECONDS: " + String(elapsed))
    print(
        "CHECKSUM: "
        + String(total_rows)
        + ":"
        + String(unique_categories)
        + ":"
        + top_category
        + ":"
        + String(top_revenue)
    )
