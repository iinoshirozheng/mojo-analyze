#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define BLOCKS 4096
#define BYTES_PER_BLOCK 32
#define ITERS 4000000
#define FNV_OFFSET UINT64_C(14695981039346656037)
#define FNV_PRIME UINT64_C(1099511628211)

static uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * UINT64_C(1000000000) + (uint64_t)ts.tv_nsec;
}

int main(void) {
    uint8_t *data = (uint8_t *)malloc((size_t)BLOCKS * BYTES_PER_BLOCK);
    if (!data) return 2;

    uint64_t state = UINT64_C(0x9E3779B97F4A7C15);
    for (int p = 0; p < BLOCKS * BYTES_PER_BLOCK; ++p) {
        state ^= state << 13;
        state ^= state >> 7;
        state ^= state << 17;
        data[p] = (uint8_t)(state & UINT64_C(0xFF));
    }

    uint64_t checksum = 0;
    uint64_t start = now_ns();
    for (int it = 0; it < ITERS; ++it) {
        int base = (it & (BLOCKS - 1)) * BYTES_PER_BLOCK;
        uint64_t h = FNV_OFFSET;
        for (int k = 0; k < BYTES_PER_BLOCK; ++k) {
            h ^= (uint64_t)data[base + k];
            h *= FNV_PRIME;
        }
        checksum ^= h + (uint64_t)it;
    }
    double elapsed = (double)(now_ns() - start) / 1000000000.0;

    printf("TIME_SECONDS: %.9f\n", elapsed);
    printf("CHECKSUM: %" PRIu64 "\n", checksum);
    free(data);
    return 0;
}
