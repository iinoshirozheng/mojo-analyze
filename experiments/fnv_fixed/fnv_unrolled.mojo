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
        h = (h ^ UInt64(data[unsafe_offset=base + 0])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 1])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 2])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 3])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 4])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 5])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 6])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 7])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 8])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 9])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 10])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 11])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 12])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 13])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 14])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 15])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 16])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 17])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 18])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 19])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 20])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 21])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 22])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 23])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 24])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 25])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 26])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 27])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 28])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 29])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 30])) * FNV_PRIME
        h = (h ^ UInt64(data[unsafe_offset=base + 31])) * FNV_PRIME
        checksum = checksum ^ (h + UInt64(it))
        it += 1
    var elapsed = Float64(perf_counter_ns() - start) / 1_000_000_000.0

    print("TIME_SECONDS:", elapsed)
    print("CHECKSUM:", checksum)
