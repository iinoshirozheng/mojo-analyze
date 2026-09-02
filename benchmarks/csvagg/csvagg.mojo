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


def main() raises:
    var csv_path = parse_csv_arg()

    var start_time = perf_counter_ns()

    var text = open(csv_path, "r").read()
    var data = text.as_bytes()
    var n = len(data)

    var revenue_by_category = Dict[String, Int]()
    var total_rows = 0

    # Skip the header line.
    var i = 0
    while i < n and data[i] != 10:  # '\n'
        i += 1
    i += 1

    var category_bytes = List[UInt8]()
    while i < n:
        # Field 0: order_id — unused, skip to the next comma.
        while i < n and data[i] != COMMA:
            i += 1
        i += 1

        # Field 1: category — the only field that needs to become a String
        # (it's the Dict key); everything else is parsed straight from bytes
        # with zero allocation, unlike the first version of this file, which
        # built a `List[String]` of all four fields per row (10M rows) even
        # though three of them were immediately discarded or parsed back to
        # Int — the same allocation-per-row mistake the original wordfreq.mojo
        # made, caught the same way: it was ~14x slower than Rust until fixed.
        category_bytes.clear()
        while i < n and data[i] != COMMA:
            category_bytes.append(data[i])
            i += 1
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
        var category = String(unsafe_from_utf8=Span(category_bytes))

        if category in revenue_by_category:
            revenue_by_category[category] = revenue_by_category[category] + revenue
        else:
            revenue_by_category[category] = revenue
        total_rows += 1

    var unique_categories = len(revenue_by_category)

    var top_category = ""
    var top_revenue = Int64(-1)
    var have_top = False
    for entry in revenue_by_category.items():
        var rev = Int64(entry.value)
        if not have_top or rev > top_revenue or (rev == top_revenue and entry.key < top_category):
            top_category = entry.key
            top_revenue = rev
            have_top = True

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
