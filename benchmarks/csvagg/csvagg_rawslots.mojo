from std.memory.alloc import unsafe_alloc
from std.sys import argv
from std.time import perf_counter_ns


def parse_csv_arg() -> String:
    var args = argv()
    var i = 1
    while i < len(args):
        if String(args[i]) == "--csv" and i + 1 < len(args):
            return String(args[i + 1])
        i += 1
    return "benchmarks/csvagg/data/orders.csv"


comptime COMMA: UInt8 = 44
comptime DIGIT_0: UInt8 = 48
comptime DIGIT_9: UInt8 = 57
comptime FNV_OFFSET: UInt64 = 14695981039346656037
comptime FNV_PRIME: UInt64 = 1099511628211
comptime CAPACITY = 1024
comptime MASK = CAPACITY - 1


def main() raises:
    var csv_path = parse_csv_arg()

    var start_time = perf_counter_ns()

    var text = open(csv_path, "r").read()
    var data = text.as_bytes()
    var n = len(data)

    # Experiment variant: identical parser, byte-span keys, FNV-1a hash,
    # open-addressing probe sequence, aggregation, and checksum to csvagg.mojo.
    # Only the five fixed-capacity slot arrays move from List[...] storage to
    # raw pointers with unsafe_offset indexing, matching the focused Category-C
    # storage experiment rather than changing hash-table semantics.
    var slot_used = unsafe_alloc[UInt8](CAPACITY)
    var slot_hash = unsafe_alloc[UInt64](CAPACITY)
    var slot_start = unsafe_alloc[Int](CAPACITY)
    var slot_end = unsafe_alloc[Int](CAPACITY)
    var slot_revenue = unsafe_alloc[Int](CAPACITY)
    # Match the canonical List(repeating=0/False, count=CAPACITY) startup work
    # instead of giving raw storage an initialization advantage.
    for s in range(CAPACITY):
        slot_used[unsafe_offset=s] = 0
        slot_hash[unsafe_offset=s] = 0
        slot_start[unsafe_offset=s] = 0
        slot_end[unsafe_offset=s] = 0
        slot_revenue[unsafe_offset=s] = 0

    var total_rows = 0

    # Skip the header line.
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

        var revenue = quantity * price_cents
        var span_len = cat_end - cat_start

        var h: UInt64 = FNV_OFFSET
        var k = cat_start
        while k < cat_end:
            h = h ^ UInt64(data[k])
            h = h * FNV_PRIME
            k += 1

        var slot = Int(h) & MASK
        while True:
            if slot_used[unsafe_offset=slot] == 0:
                slot_used[unsafe_offset=slot] = 1
                slot_hash[unsafe_offset=slot] = h
                slot_start[unsafe_offset=slot] = cat_start
                slot_end[unsafe_offset=slot] = cat_end
                slot_revenue[unsafe_offset=slot] = 0
                break

            var matches = False
            if (
                slot_hash[unsafe_offset=slot] == h
                and (
                    slot_end[unsafe_offset=slot]
                    - slot_start[unsafe_offset=slot]
                ) == span_len
            ):
                matches = True
                var j = 0
                while j < span_len:
                    if (
                        data[slot_start[unsafe_offset=slot] + j]
                        != data[cat_start + j]
                    ):
                        matches = False
                        break
                    j += 1

            if matches:
                break
            slot = (slot + 1) & MASK

        slot_revenue[unsafe_offset=slot] = (
            slot_revenue[unsafe_offset=slot] + revenue
        )
        total_rows += 1

    var unique_categories = 0
    var top_category = ""
    var top_revenue = Int64(-1)
    var have_top = False

    var s = 0
    while s < CAPACITY:
        if slot_used[unsafe_offset=s] == 1:
            unique_categories += 1
            var buf = List[UInt8]()
            var p = slot_start[unsafe_offset=s]
            while p < slot_end[unsafe_offset=s]:
                buf.append(data[p])
                p += 1
            var category = String(unsafe_from_utf8=Span(buf))
            var rev = Int64(slot_revenue[unsafe_offset=s])
            if (
                not have_top
                or rev > top_revenue
                or (rev == top_revenue and category < top_category)
            ):
                top_category = category
                top_revenue = rev
                have_top = True
        s += 1

    var elapsed_ns = perf_counter_ns() - start_time
    var elapsed = Float64(elapsed_ns) / 1_000_000_000.0

    # Keep deallocation outside the timed region, matching the canonical List
    # variant whose destructors execute after its timer stops.
    slot_used.unsafe_free()
    slot_hash.unsafe_free()
    slot_start.unsafe_free()
    slot_end.unsafe_free()
    slot_revenue.unsafe_free()

    print("TIME_SECONDS:", elapsed)
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
