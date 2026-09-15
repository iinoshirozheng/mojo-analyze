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
comptime FNV_OFFSET: UInt64 = 14695981039346656037
comptime FNV_PRIME: UInt64 = 1099511628211


def main() raises:
    var csv_path = parse_csv_arg()
    var start_time = perf_counter_ns()

    var text = open(csv_path, "r").read()
    var data = text.as_bytes()
    var n = len(data)

    var total_rows = 0
    var revenue_sum: Int64 = 0
    var hash_xor: UInt64 = 0
    var category_bytes_total: Int64 = 0

    # Skip the header line exactly as the canonical Category-D implementation.
    var i = 0
    while i < n and data[i] != 10:
        i += 1
    i += 1

    while i < n:
        # Field 0: order_id — unused, skip to comma.
        while i < n and data[i] != COMMA:
            i += 1
        i += 1

        # Field 1: category — same raw byte-span capture as canonical csvagg.
        var cat_start = i
        while i < n and data[i] != COMMA:
            i += 1
        var cat_end = i
        i += 1

        # Field 2: quantity — same digit parser.
        var quantity = 0
        while i < n and data[i] != COMMA:
            quantity = quantity * 10 + Int(data[i] - DIGIT_0)
            i += 1
        i += 1

        # Field 3: price_cents — same digit parser and end-of-line handling.
        var price_cents = 0
        while i < n and data[i] != COMMA and data[i] != 10:
            price_cents = price_cents * 10 + Int(data[i] - DIGIT_0)
            i += 1
        while i < n and data[i] != 10:
            i += 1
        i += 1

        # Same variable-length FNV-1a loop as canonical csvagg.mojo. The
        # experiment stops here: no table slot lookup, probing, equality, or
        # aggregation into per-category state.
        var h: UInt64 = FNV_OFFSET
        var k = cat_start
        while k < cat_end:
            h = h ^ UInt64(data[k])
            h = h * FNV_PRIME
            k += 1

        total_rows += 1
        revenue_sum += Int64(quantity * price_cents)
        hash_xor = hash_xor ^ h
        category_bytes_total += Int64(cat_end - cat_start)

    var elapsed_ns = perf_counter_ns() - start_time
    var elapsed = Float64(elapsed_ns) / 1_000_000_000.0

    print("TIME_SECONDS:", elapsed)
    print(
        "CHECKSUM: "
        + String(total_rows)
        + ":"
        + String(hash_xor)
        + ":"
        + String(revenue_sum)
        + ":"
        + String(category_bytes_total)
    )
