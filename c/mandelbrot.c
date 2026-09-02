// Compile: clang -O3 -ffp-contract=off -o dist/mandelbrot-c c/mandelbrot.c
// -ffp-contract=off is required, not optional: plain `-O3` on this Apple
// clang DOES auto-contract `zr*zr - zi*zi + re` into an FMA by default
// (confirmed empirically — without the flag the checksum drifted from
// 42411634 to 42411589 at the default size). Same lesson this repo already
// learned once from Mojo's default build; C reproduces it here too.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static const double RE_MIN = -2.0;
static const double RE_MAX = 1.0;
static const double IM_MIN = -1.5;
static const double IM_MAX = 1.5;

int main(int argc, char **argv) {
    long width = 800, height = 600, max_iter = 500;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--width") == 0 && i + 1 < argc) {
            width = atol(argv[++i]);
        } else if (strcmp(argv[i], "--height") == 0 && i + 1 < argc) {
            height = atol(argv[++i]);
        } else if (strcmp(argv[i], "--max-iter") == 0 && i + 1 < argc) {
            max_iter = atol(argv[++i]);
        }
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    long w_div = (width - 1 < 1) ? 1 : width - 1;
    long h_div = (height - 1 < 1) ? 1 : height - 1;
    double dre = (RE_MAX - RE_MIN) / (double)w_div;
    double dim = (IM_MAX - IM_MIN) / (double)h_div;

    long long total = 0;
    for (long y = 0; y < height; y++) {
        double im = IM_MAX - dim * (double)y;
        for (long x = 0; x < width; x++) {
            double re = RE_MIN + dre * (double)x;
            double zr = 0.0, zi = 0.0;
            long cnt = 0;
            while (cnt < max_iter && zr * zr + zi * zi <= 4.0) {
                double new_zr = zr * zr - zi * zi + re;
                zi = 2.0 * zr * zi + im;
                zr = new_zr;
                cnt++;
            }
            total += cnt;
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;

    printf("TIME_SECONDS: %.9f\n", elapsed);
    printf("CHECKSUM: %lld\n", total);
    return 0;
}
