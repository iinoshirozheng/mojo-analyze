from std.sys import argv
from std.time import perf_counter_ns

comptime RE_MIN: Float64 = -2.0
comptime RE_MAX: Float64 = 1.0
comptime IM_MIN: Float64 = -1.5
comptime IM_MAX: Float64 = 1.5
comptime LANES = 4


def parse_int(s: String) raises -> Int:
    return Int(s)


def compute(width: Int, height: Int, max_iter: Int) -> Int64:
    var w_div = width - 1
    if w_div < 1:
        w_div = 1
    var h_div = height - 1
    if h_div < 1:
        h_div = 1

    var dre = (RE_MAX - RE_MIN) / Float64(w_div)
    var dim = (IM_MAX - IM_MIN) / Float64(h_div)

    var total: Int64 = 0

    for y in range(height):
        var im = IM_MAX - dim * Float64(y)
        var x = 0

        while x + LANES <= width:
            var re_vec = SIMD[DType.float64, LANES](0.0, 0.0, 0.0, 0.0)
            for lane in range(LANES):
                re_vec[lane] = RE_MIN + dre * Float64(x + lane)
            var im_vec = SIMD[DType.float64, LANES](im, im, im, im)
            var zr = SIMD[DType.float64, LANES](0.0, 0.0, 0.0, 0.0)
            var zi = SIMD[DType.float64, LANES](0.0, 0.0, 0.0, 0.0)
            var count = SIMD[DType.int64, LANES](0, 0, 0, 0)
            var active = SIMD[DType.bool, LANES](True, True, True, True)

            for _ in range(max_iter):
                var active_count = Int(active.cast[DType.uint8]().reduce_add())
                if active_count == 0:
                    break

                var new_zr = zr * zr - zi * zi + re_vec
                var new_zi = 2.0 * zr * zi + im_vec
                var mag2 = new_zr * new_zr + new_zi * new_zi
                var still = mag2.le(4.0)

                zr = active.select(new_zr, zr)
                zi = active.select(new_zi, zi)
                count = active.select(count + 1, count)
                active = active & still

            for lane in range(LANES):
                total += Int64(count[lane])
            x += LANES

        while x < width:
            var re = RE_MIN + dre * Float64(x)
            var zr_s: Float64 = 0.0
            var zi_s: Float64 = 0.0
            var cnt = 0
            while cnt < max_iter and zr_s * zr_s + zi_s * zi_s <= 4.0:
                var new_zr_s = zr_s * zr_s - zi_s * zi_s + re
                zi_s = 2.0 * zr_s * zi_s + im
                zr_s = new_zr_s
                cnt += 1
            total += Int64(cnt)
            x += 1

    return total


def main() raises:
    var width = 800
    var height = 600
    var max_iter = 500

    var args = argv()
    var i = 1
    while i < len(args):
        var flag = String(args[i])
        if flag == "--width" and i + 1 < len(args):
            width = parse_int(String(args[i + 1]))
            i += 2
        elif flag == "--height" and i + 1 < len(args):
            height = parse_int(String(args[i + 1]))
            i += 2
        elif flag == "--max-iter" and i + 1 < len(args):
            max_iter = parse_int(String(args[i + 1]))
            i += 2
        else:
            i += 1

    var start = perf_counter_ns()
    var total = compute(width, height, max_iter)
    var elapsed_ns = perf_counter_ns() - start
    var elapsed_s = Float64(elapsed_ns) / 1_000_000_000.0

    print("TIME_SECONDS:", elapsed_s)
    print("CHECKSUM:", total)
