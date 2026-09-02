// Compile: clang -O3 -o dist/sieve-c c/sieve.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

int main(int argc, char **argv) {
    long limit = 50000000;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--limit") == 0 && i + 1 < argc) {
            limit = atol(argv[++i]);
        }
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    unsigned char *is_prime = malloc((size_t)(limit + 1));
    memset(is_prime, 1, (size_t)(limit + 1));
    is_prime[0] = 0;
    if (limit >= 1) is_prime[1] = 0;

    for (long i = 2; i * i <= limit; i++) {
        if (is_prime[i]) {
            for (long j = i * i; j <= limit; j += i) {
                is_prime[j] = 0;
            }
        }
    }

    long long count = 0;
    long long total = 0;
    for (long idx = 2; idx <= limit; idx++) {
        if (is_prime[idx]) {
            count++;
            total += idx;
        }
    }
    free(is_prime);

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;
    long long sum_mod = total % 1000000007LL;

    printf("TIME_SECONDS: %.9f\n", elapsed);
    printf("CHECKSUM: %lld:%lld\n", count, sum_mod);
    return 0;
}
