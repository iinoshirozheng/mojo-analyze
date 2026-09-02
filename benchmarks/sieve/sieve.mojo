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

    # Raw-pointer version: `alloc[T](n)` still emits a "Layout-based alloc"
    # deprecation warning on this stable (1.0.x) toolchain — the compiler's
    # suggested replacement, `unsafe_alloc`, does not actually resolve as a
    # symbol anywhere in this release (checked: not in the prelude, not under
    # `std.memory`/`std.sys`, not a static method on `Pointer`/`UnsafePointer`)
    # — so `alloc` + unsafe indexing is the best currently-achievable raw
    # pointer path; `p[unsafe_offset=i]` indexing and `.unsafe_free()` are
    # both clean (no warnings) on top of it. The whole point of this rewrite
    # is to skip List's per-element bounds check in the hot marking loop.
    var is_prime = alloc[UInt8](limit + 1)
    for idx in range(limit + 1):
        is_prime[unsafe_offset=idx] = 1
    is_prime[unsafe_offset=0] = 0
    if limit >= 1:
        is_prime[unsafe_offset=1] = 0

    var i = 2
    while i * i <= limit:
        if is_prime[unsafe_offset=i] == 1:
            var j = i * i
            while j <= limit:
                is_prime[unsafe_offset=j] = 0
                j += i
        i += 1

    var count = 0
    var total = 0
    for idx in range(2, limit + 1):
        if is_prime[unsafe_offset=idx] == 1:
            count += 1
            total += idx

    is_prime.unsafe_free()

    var elapsed_ns = perf_counter_ns() - start_ns
    var elapsed_s = Float64(elapsed_ns) / 1_000_000_000.0

    var sum_mod = total % 1_000_000_007

    print("TIME_SECONDS:", elapsed_s)
    print("CHECKSUM: " + String(count) + ":" + String(sum_mod))
