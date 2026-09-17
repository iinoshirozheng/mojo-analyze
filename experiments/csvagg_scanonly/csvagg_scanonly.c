#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

int main(int argc, char **argv) {
    const char *csv_path = "benchmarks/csvagg/data/orders.csv";
    for (int a = 1; a < argc; a++) {
        if (strcmp(argv[a], "--csv") == 0 && a + 1 < argc) csv_path = argv[++a];
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    FILE *f = fopen(csv_path, "rb");
    if (!f) { fprintf(stderr, "cannot open %s\n", csv_path); return 1; }
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    unsigned char *data = malloc((size_t)n);
    fread(data, 1, (size_t)n, f);
    fclose(f);

    long long total_rows = 0;
    long long order_id_bytes_total = 0;
    long long category_bytes_total = 0;
    long long quantity_bytes_total = 0;
    long long price_bytes_total = 0;

    long i = 0;
    while (i < n && data[i] != '\n') i++;
    i++;

    while (i < n) {
        long order_start = i;
        while (i < n && data[i] != ',') i++;
        long order_end = i;
        i++;

        long cat_start = i;
        while (i < n && data[i] != ',') i++;
        long cat_end = i;
        i++;

        long quantity_start = i;
        while (i < n && data[i] != ',') i++;
        long quantity_end = i;
        i++;

        long price_start = i;
        while (i < n && data[i] != '\n') i++;
        long price_end = i;
        i++;

        total_rows++;
        order_id_bytes_total += order_end - order_start;
        category_bytes_total += cat_end - cat_start;
        quantity_bytes_total += quantity_end - quantity_start;
        price_bytes_total += price_end - price_start;
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;

    printf("TIME_SECONDS: %.9f\n", elapsed);
    printf("CHECKSUM: %lld:%lld:%lld:%lld:%lld\n",
           total_rows, order_id_bytes_total, category_bytes_total,
           quantity_bytes_total, price_bytes_total);
    free(data);
    return 0;
}
