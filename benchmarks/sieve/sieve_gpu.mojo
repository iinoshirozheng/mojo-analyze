# GPU primality test, NOT a GPU sieve -- disclosed honestly, same spirit as
# mandelbrot_gpu.mojo's Float32 disclosure. A classic Sieve of Eratosthenes's
# marking phase is a poor GPU fit: different primes have wildly different
# amounts of marking work (2 has ~limit/2 multiples, a prime near sqrt(limit)
# has only a handful), so a naive one-thread-per-prime mapping is badly
# load-imbalanced. Instead: one GPU thread per CANDIDATE number, each doing
# trial division against a small precomputed list of primes up to sqrt(limit)
# (computed cheaply on the CPU with a tiny serial sieve first, then uploaded).
# This is embarrassingly parallel and load-balanced (every thread does
# roughly comparable early-exit-on-first-divisor work), but it is a
# genuinely DIFFERENT algorithm -- O(n * pi(sqrt(n))) trial-division work
# instead of the CPU sieve's O(n log log n) marking work -- not the same
# algorithm merely parallelized. The final set of primes (and therefore the
# checksum) is identical either way, since "is n prime" has one right answer
# regardless of method.
from std.sys import argv
from std.sys.info import has_accelerator
from std.time import perf_counter_ns
from std.math import ceildiv
from std.gpu import global_idx
from max.gpu.host import DeviceContext
from layout import TileTensor, TensorLayout, row_major

comptime BLOCK = 256


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


def int_sqrt(n: Int) -> Int:
    from std.math import sqrt
    var r = Int(sqrt(Float64(n)))
    while r * r > n:
        r -= 1
    while (r + 1) * (r + 1) <= n:
        r += 1
    return r


def small_primes_up_to(bound: Int) -> List[Int32]:
    # Tiny serial sieve, e.g. bound ~= sqrt(50_000_000) ~= 7071 -- negligible
    # CPU cost compared to the GPU pass over the full candidate range.
    var is_prime = List[Bool](length=bound + 1, fill=True)
    if bound >= 0:
        is_prime[0] = False
    if bound >= 1:
        is_prime[1] = False
    var i = 2
    while i * i <= bound:
        if is_prime[i]:
            var j = i * i
            while j <= bound:
                is_prime[j] = False
                j += i
        i += 1
    var primes = List[Int32]()
    for idx in range(2, bound + 1):
        if is_prime[idx]:
            primes.append(Int32(idx))
    return primes^


def primality_kernel[
    LT: TensorLayout, PT: TensorLayout
](
    output: TileTensor[DType.uint8, LT, MutAnyOrigin],
    small_primes: TileTensor[DType.int32, PT, MutAnyOrigin],
    num_small_primes: Int32,
    limit: Int32,
):
    comptime assert output.flat_rank == 1, "expected 1D output"
    comptime assert small_primes.flat_rank == 1, "expected 1D small_primes"
    var idx = global_idx.x
    var n = Int32(idx) + 2  # candidates start at 2
    if n > limit:
        return
    var is_p: UInt8 = 1
    var p_idx: Int32 = 0
    while p_idx < num_small_primes:
        var p = rebind[Int32](small_primes[Int(p_idx)])
        if p * p > n:
            break
        if n % p == 0:
            is_p = 0
            break
        p_idx += 1
    output[idx] = is_p


def main() raises:
    comptime assert has_accelerator(), "Requires a GPU"

    var limit = parse_limit()
    var bound = int_sqrt(limit)
    var host_small_primes = small_primes_up_to(bound)
    var num_small_primes = len(host_small_primes)

    var ctx = DeviceContext()
    var n_candidates = limit - 1  # candidates 2..limit inclusive

    var start = perf_counter_ns()

    var primes_buf = ctx.enqueue_create_buffer[DType.int32](num_small_primes)
    with primes_buf.map_to_host() as mapped:
        var host_view = TileTensor(mapped, row_major(num_small_primes))
        for i in range(num_small_primes):
            host_view[i] = host_small_primes[i]

    var out_buf = ctx.enqueue_create_buffer[DType.uint8](n_candidates)
    var out_layout = row_major(n_candidates)
    var primes_layout = row_major(num_small_primes)
    var output = TileTensor(out_buf, out_layout)
    var small_primes_t = TileTensor(primes_buf, primes_layout)

    comptime kernel = primality_kernel[type_of(out_layout), type_of(primes_layout)]
    ctx.enqueue_function[kernel](
        output, small_primes_t, Int32(num_small_primes), Int32(limit),
        grid_dim=ceildiv(n_candidates, BLOCK),
        block_dim=BLOCK,
    )

    var count: Int64 = 0
    var total: Int64 = 0
    with out_buf.map_to_host() as mapped:
        var host = TileTensor(mapped, out_layout)
        for i in range(n_candidates):
            if host[i] == 1:
                count += 1
                total += Int64(i + 2)

    var elapsed_ns = perf_counter_ns() - start
    var elapsed_s = Float64(elapsed_ns) / 1_000_000_000.0
    var sum_mod = total % 1_000_000_007

    print("TIME_SECONDS:", elapsed_s)
    print("CHECKSUM: " + String(count) + ":" + String(sum_mod))
