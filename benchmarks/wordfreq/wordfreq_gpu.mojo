# Disclosed CPU/GPU split, same spirit as mandelbrot_gpu.mojo's precision
# disclosure and sieve_gpu.mojo's algorithm disclosure: a full concurrent
# hash-table build (many threads racing to insert into a shared table with
# collision resolution) is a genuinely hard GPU problem, and a naive
# unsynchronized version would just be wrong. So: the CPU does file read +
# tokenize + FNV-1a hash + open-addressing SLOT RESOLUTION (deciding which
# of 8192 buckets each token belongs to, resolving collisions the same way
# the CPU-only wordfreq.mojo does) -- producing one Int32 bucket-id per
# token. The GPU's job is the part that's actually easy to parallelize once
# bucket ids are known: one thread per token, atomicAdd(counts[bucket_id], 1).
# TIME_SECONDS covers the WHOLE pipeline (file read through final top-word
# lookup, matching every other benchmark's file-read-included convention for
# this category) -- not just the GPU kernel -- so this number is directly
# comparable to the pure-CPU wordfreq.mojo's 0.298s, and honestly shows the
# GPU dispatch/transfer overhead sitting on top of CPU work that's still
# mostly serial (the hashing/probing isn't offloaded, only the final count).
from std.sys import argv
from std.sys.info import has_accelerator
from std.time import perf_counter_ns
from std.math import ceildiv
from std.gpu import global_idx
from max.gpu.host import DeviceContext
from max.gpu.sync import barrier
from std.atomic import Atomic
from layout import TileTensor, TensorLayout, row_major

comptime CAPACITY = 8192
comptime MASK = CAPACITY - 1
comptime BLOCK = 256
comptime FNV_OFFSET: UInt64 = 14695981039346656037
comptime FNV_PRIME: UInt64 = 1099511628211
comptime ASCII_a: UInt8 = 97
comptime ASCII_z: UInt8 = 122
comptime ASCII_A: UInt8 = 65
comptime ASCII_Z: UInt8 = 90
comptime ASCII_0: UInt8 = 48
comptime ASCII_9: UInt8 = 57


def is_alnum_byte(b: UInt8) -> Bool:
    return (
        (b >= ASCII_a and b <= ASCII_z)
        or (b >= ASCII_A and b <= ASCII_Z)
        or (b >= ASCII_0 and b <= ASCII_9)
    )


def lower_byte(b: UInt8) -> UInt8:
    if b >= ASCII_A and b <= ASCII_Z:
        return b + 32
    return b


def parse_corpus_arg() -> String:
    var args = argv()
    var i = 1
    while i < len(args):
        if String(args[i]) == "--corpus" and i + 1 < len(args):
            return String(args[i + 1])
        i += 1
    return "benchmarks/wordfreq/data/corpus.txt"


def count_kernel[
    BT: TensorLayout, CT: TensorLayout
](
    bucket_ids: TileTensor[DType.int32, BT, MutAnyOrigin],
    counts: TileTensor[DType.int32, CT, MutAnyOrigin],
    total_tokens: Int32,
):
    comptime assert bucket_ids.flat_rank == 1, "expected 1D bucket_ids"
    comptime assert counts.flat_rank == 1, "expected 1D counts"
    var idx = global_idx.x
    if idx < Int(total_tokens):
        var b = rebind[Int32](bucket_ids[Int(idx)])
        # `ptr + offset` still emits a deprecation warning on this stable
        # release (same "Layout-based alloc/pointer migration in progress"
        # situation sieve.mojo's raw-pointer rewrite already documented) --
        # `ptr[unsafe_offset=i]` indexes a *value* at an offset, but
        # Atomic.fetch_add needs an offset *pointer*, and no non-deprecated
        # way to form one exists yet on this toolchain. Accepted, disclosed.
        _ = Atomic.fetch_add(counts.ptr + Int(b), 1)


def main() raises:
    comptime assert has_accelerator(), "Requires a GPU"

    var corpus_path = parse_corpus_arg()

    var start = perf_counter_ns()

    var text = open(corpus_path, "r").read()
    var data = text.as_bytes()
    var n = len(data)

    # CPU pass: tokenize + hash + resolve each token to a bucket id, exactly
    # like the CPU-only version's hash table construction -- but recording
    # the bucket id per token instead of incrementing a counter here.
    var slot_used = List[Bool](length=CAPACITY, fill=False)
    var slot_hash = List[UInt64](length=CAPACITY, fill=0)
    var slot_start = List[Int](length=CAPACITY, fill=0)
    var slot_end = List[Int](length=CAPACITY, fill=0)
    var bucket_ids = List[Int32]()

    var idx = 0
    var token_start = -1
    while idx <= n:
        var at_boundary = True
        if idx < n:
            if is_alnum_byte(data[idx]):
                at_boundary = False

        if at_boundary:
            if token_start >= 0:
                var tok_start = token_start
                var tok_end = idx
                var span_len = tok_end - tok_start

                var h: UInt64 = FNV_OFFSET
                var i = tok_start
                while i < tok_end:
                    h = h ^ UInt64(lower_byte(data[i]))
                    h = h * FNV_PRIME
                    i += 1

                var slot = Int(h) & MASK
                while True:
                    if not slot_used[slot]:
                        slot_used[slot] = True
                        slot_hash[slot] = h
                        slot_start[slot] = tok_start
                        slot_end[slot] = tok_end
                        break
                    var matches = False
                    if slot_hash[slot] == h and (slot_end[slot] - slot_start[slot]) == span_len:
                        matches = True
                        var j = 0
                        while j < span_len:
                            if lower_byte(data[slot_start[slot] + j]) != lower_byte(data[tok_start + j]):
                                matches = False
                                break
                            j += 1
                    if matches:
                        break
                    slot = (slot + 1) & MASK

                bucket_ids.append(Int32(slot))
                token_start = -1
        else:
            if token_start < 0:
                token_start = idx
        idx += 1

    var total_tokens = len(bucket_ids)

    var ctx = DeviceContext()
    var ids_buf = ctx.enqueue_create_buffer[DType.int32](total_tokens)
    with ids_buf.map_to_host() as mapped:
        var host_view = TileTensor(mapped, row_major(total_tokens))
        for i in range(total_tokens):
            host_view[i] = bucket_ids[i]

    var counts_buf = ctx.enqueue_create_buffer[DType.int32](CAPACITY)
    counts_buf.enqueue_fill(0)

    var ids_layout = row_major(total_tokens)
    var counts_layout = row_major(CAPACITY)
    var ids_t = TileTensor(ids_buf, ids_layout)
    var counts_t = TileTensor(counts_buf, counts_layout)

    comptime kernel = count_kernel[type_of(ids_layout), type_of(counts_layout)]
    ctx.enqueue_function[kernel](
        ids_t, counts_t, Int32(total_tokens),
        grid_dim=ceildiv(total_tokens, BLOCK),
        block_dim=BLOCK,
    )

    var unique_words = 0
    var top_word = ""
    var top_count: Int64 = -1
    with counts_buf.map_to_host() as mapped:
        var host_counts = TileTensor(mapped, counts_layout)
        var s = 0
        while s < CAPACITY:
            if slot_used[s]:
                unique_words += 1
                var cnt = Int64(host_counts[s])
                var buf = List[UInt8]()
                var p = slot_start[s]
                while p < slot_end[s]:
                    buf.append(lower_byte(data[p]))
                    p += 1
                var word = String(unsafe_from_utf8=Span(buf))
                if top_count < 0 or cnt > top_count or (cnt == top_count and word < top_word):
                    top_word = word
                    top_count = cnt
            s += 1

    var elapsed_ns = perf_counter_ns() - start
    var elapsed = Float64(elapsed_ns) / 1_000_000_000.0

    print("TIME_SECONDS: " + String(elapsed))
    print(
        "CHECKSUM: "
        + String(total_tokens)
        + ":"
        + String(unique_words)
        + ":"
        + top_word
        + ":"
        + String(top_count)
    )
