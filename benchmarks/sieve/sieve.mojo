from std.sys import argv
from std.time import perf_counter_ns


def parse_limit() raises -> Int:
    var args = argv()
    var limit = 50_000_000
    var i = 1
    while i < len(args):
        if String(args[i]) == "--limit" and i + 1 < len(args):
            limit = Int(args[i + 1])
            i += 2
        else:
            i += 1
    return limit


def main() raises:
    var limit = parse_limit()

    var start_ns = perf_counter_ns()

    var is_prime = List[UInt8](length=limit + 1, fill=1)
    is_prime[0] = 0
    if limit >= 1:
        is_prime[1] = 0

    var i = 2
    while i * i <= limit:
        if is_prime[i] == 1:
            var j = i * i
            while j <= limit:
                is_prime[j] = 0
                j += i
        i += 1

    var count = 0
    var total = 0
    for idx in range(2, limit + 1):
        if is_prime[idx] == 1:
            count += 1
            total += idx

    var elapsed_ns = perf_counter_ns() - start_ns
    var elapsed_s = Float64(elapsed_ns) / 1_000_000_000.0

    var sum_mod = total % 1_000_000_007

    print("TIME_SECONDS:", elapsed_s)
    print("CHECKSUM: " + String(count) + ":" + String(sum_mod))
