from std.memory.alloc import unsafe_alloc
from std.time import perf_counter_ns


comptime BLOCKS = 4096
comptime BYTES_PER_BLOCK = 32
comptime ITERS = 4_000_000
comptime FNV_OFFSET: UInt64 = 14695981039346656037
comptime FNV_PRIME: UInt64 = 1099511628211


def main() raises:
    var data = unsafe_alloc[UInt8](BLOCKS * BYTES_PER_BLOCK)
    var state: UInt64 = 0x9E3779B97F4A7C15
    var p = 0
    while p < BLOCKS * BYTES_PER_BLOCK:
        state = state ^ (state << 13)
        state = state ^ (state >> 7)
        state = state ^ (state << 17)
        data[unsafe_offset=p] = UInt8(state & 0xFF)
        p += 1

    var checksum: UInt64 = 0
    var start = perf_counter_ns()
    var it = 0
    while it < ITERS:
        var base = (it & (BLOCKS - 1)) * BYTES_PER_BLOCK
        var h: UInt64 = FNV_OFFSET
        var k = 0
        while k < BYTES_PER_BLOCK:
            h = h ^ UInt64(data[unsafe_offset=base + k])
            h = h * FNV_PRIME
            k += 1
        checksum = checksum ^ (h + UInt64(it))
        it += 1
    var elapsed = Float64(perf_counter_ns() - start) / 1_000_000_000.0

    print("TIME_SECONDS:", elapsed)
    print("CHECKSUM:", checksum)
