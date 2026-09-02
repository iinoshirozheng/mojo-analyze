from std.sys import argv
from std.sys.info import has_accelerator
from std.time import perf_counter_ns
from std.math import ceildiv
from std.gpu import global_idx
from max.gpu.host import DeviceContext
from layout import TileTensor, TensorLayout, row_major

# Metal has no `double` type (Apple GPUs don't support IEEE-754 float64 in
# compute kernels — "double is not supported... Metal-unsupported
# instructions" from the backend). The GPU kernel runs in Float32; the CPU
# reference implementation runs in Float64. This is a hardware limitation,
# not a bug — an exact checksum match across the two is not achievable, so
# this kernel is intentionally NOT held to the cross-language checksum gate
# the rest of this repo uses. See ANALYSIS.md for the precision discussion.
comptime RE_MIN: Float32 = -2.0
comptime RE_MAX: Float32 = 1.0
comptime IM_MIN: Float32 = -1.5
comptime IM_MAX: Float32 = 1.5
comptime BLOCK = 256


def parse_int(s: String) raises -> Int:
    return Int(s)


def mandelbrot_kernel[
    LT: TensorLayout
](
    output: TileTensor[DType.int32, LT, MutAnyOrigin],
    width: Int32,
    height: Int32,
    max_iter: Int32,
    dre: Float32,
    dim: Float32,
):
    comptime assert output.flat_rank == 1, "expected 1D output"
    var idx = global_idx.x
    var n = Int(width) * Int(height)
    if idx < n:
        var x = Int32(idx) % width
        var y = Int32(idx) // width
        var re = RE_MIN + dre * Float32(x)
        var im = IM_MAX - dim * Float32(y)
        var zr: Float32 = 0.0
        var zi: Float32 = 0.0
        var cnt: Int32 = 0
        while cnt < Int32(max_iter) and zr * zr + zi * zi <= 4.0:
            var new_zr = zr * zr - zi * zi + re
            zi = 2.0 * zr * zi + im
            zr = new_zr
            cnt += 1
        output[idx] = rebind[output.ElementType](cnt)


def main() raises:
    comptime assert has_accelerator(), "Requires a GPU"

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

    var w_div = width - 1
    if w_div < 1:
        w_div = 1
    var h_div = height - 1
    if h_div < 1:
        h_div = 1
    var dre = (RE_MAX - RE_MIN) / Float32(w_div)
    var dim_step = (IM_MAX - IM_MIN) / Float32(h_div)

    var ctx = DeviceContext()
    var n = width * height

    var start = perf_counter_ns()

    var out_buf = ctx.enqueue_create_buffer[DType.int32](n)
    var layout = row_major(n)
    var output = TileTensor(out_buf, layout)

    comptime kernel = mandelbrot_kernel[type_of(layout)]
    ctx.enqueue_function[kernel](
        output, Int32(width), Int32(height), Int32(max_iter), dre, dim_step,
        grid_dim=ceildiv(n, BLOCK),
        block_dim=BLOCK,
    )

    var total: Int64 = 0
    with out_buf.map_to_host() as mapped:
        var host = TileTensor(mapped, layout)
        for idx in range(n):
            total += Int64(host[idx])

    var elapsed_ns = perf_counter_ns() - start
    var elapsed_s = Float64(elapsed_ns) / 1_000_000_000.0

    print("TIME_SECONDS:", elapsed_s)
    print("CHECKSUM:", total)
