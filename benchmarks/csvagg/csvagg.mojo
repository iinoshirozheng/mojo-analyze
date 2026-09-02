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

    # Byte-span open-addressing hash table keyed by the category field's raw
    # (start, end) offsets into `data` — no per-row String allocation. This
    # is the same fix that already took wordfreq.mojo from 2.15s (slowest of
    # three) to 0.298s (fastest of three): `Dict[String, Int]` needed a fresh
    # String built from `category_bytes` on every one of 10M rows just to use
    # as a lookup key. Hashing/comparing the category's raw bytes in place
    # skips that entirely — a String is only ever built for the <=99 *unique*
    # categories, in the small summary loop at the end, not in the hot loop.
    var slot_used = List[Bool](length=CAPACITY, fill=False)
    var slot_hash = List[UInt64](length=CAPACITY, fill=0)
    var slot_start = List[Int](length=CAPACITY, fill=0)
    var slot_end = List[Int](length=CAPACITY, fill=0)
    var slot_revenue = List[Int](length=CAPACITY, fill=0)
    var total_rows = 0

    # Skip the header line.
    var i = 0
    while i < n and data[i] != 10:  # '\n'
        i += 1
    i += 1

    while i < n:
        # Field 0: order_id — unused, skip to the next comma.
        while i < n and data[i] != COMMA:
            i += 1
        i += 1

        # Field 1: category — captured as a (start, end) byte span. Never
        # copied into a buffer, never turned into a String, in this loop.
        var cat_start = i
        while i < n and data[i] != COMMA:
            i += 1
        var cat_end = i
        i += 1

        # Field 2: quantity — parse digits directly, no String.
        var quantity = 0
        while i < n and data[i] != COMMA:
            quantity = quantity * 10 + Int(data[i] - DIGIT_0)
            i += 1
        i += 1

        # Field 3: price_cents — parse digits directly, stop at newline/EOF.
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
            if not slot_used[slot]:
                slot_used[slot] = True
                slot_hash[slot] = h
                slot_start[slot] = cat_start
                slot_end[slot] = cat_end
                slot_revenue[slot] = 0
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
            slot = (slot + 1) & MASK

        slot_revenue[slot] = slot_revenue[slot] + revenue
        total_rows += 1

    var unique_categories = 0
    var top_category = ""
    var top_revenue = Int64(-1)
    var have_top = False

    var s = 0
    while s < CAPACITY:
        if slot_used[s]:
            unique_categories += 1
            var buf = List[UInt8]()
            var p = slot_start[s]
            while p < slot_end[s]:
                buf.append(data[p])
                p += 1
            var category = String(unsafe_from_utf8=Span(buf))
            var rev = Int64(slot_revenue[s])
            if not have_top or rev > top_revenue or (rev == top_revenue and category < top_category):
                top_category = category
                top_revenue = rev
                have_top = True
        s += 1

    var elapsed_ns = perf_counter_ns() - start_time
    var elapsed = Float64(elapsed_ns) / 1_000_000_000.0

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
