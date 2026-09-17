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
comptime NEWLINE: UInt8 = 10


def main() raises:
    var csv_path = parse_csv_arg()
    var start_time = perf_counter_ns()

    var text = open(csv_path, "r").read()
    var data = text.as_bytes()
    var n = len(data)

    var total_rows = 0
    var order_id_bytes_total: Int64 = 0
    var category_bytes_total: Int64 = 0
    var quantity_bytes_total: Int64 = 0
    var price_bytes_total: Int64 = 0

    # Preserve Category-D file read and delimiter scanning, but remove all
    # quantity/price digit-to-integer accumulation and revenue arithmetic.
    var i = 0
    while i < n and data[i] != NEWLINE:
        i += 1
    i += 1

    while i < n:
        var order_start = i
        while i < n and data[i] != COMMA:
            i += 1
        var order_end = i
        i += 1

        var cat_start = i
        while i < n and data[i] != COMMA:
            i += 1
        var cat_end = i
        i += 1

        var quantity_start = i
        while i < n and data[i] != COMMA:
            i += 1
        var quantity_end = i
        i += 1

        var price_start = i
        while i < n and data[i] != NEWLINE:
            i += 1
        var price_end = i
        i += 1

        total_rows += 1
        order_id_bytes_total += Int64(order_end - order_start)
        category_bytes_total += Int64(cat_end - cat_start)
        quantity_bytes_total += Int64(quantity_end - quantity_start)
        price_bytes_total += Int64(price_end - price_start)

    var elapsed_ns = perf_counter_ns() - start_time
    var elapsed = Float64(elapsed_ns) / 1_000_000_000.0

    print("TIME_SECONDS:", elapsed)
    print(
        "CHECKSUM: "
        + String(total_rows)
        + ":"
        + String(order_id_bytes_total)
        + ":"
        + String(category_bytes_total)
        + ":"
        + String(quantity_bytes_total)
        + ":"
        + String(price_bytes_total)
    )
