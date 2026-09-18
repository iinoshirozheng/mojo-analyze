#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static unsigned char *load_file(const char *path, long *n_out) {
    FILE *f = fopen(path, "rb");
    if (!f) { fprintf(stderr, "cannot open %s\n", path); exit(1); }
    if (fseek(f, 0, SEEK_END) != 0) exit(2);
    long n = ftell(f);
    if (n < 0) exit(3);
    if (fseek(f, 0, SEEK_SET) != 0) exit(4);
    unsigned char *data = malloc((size_t)n);
    if (!data) exit(5);
    size_t got = fread(data, 1, (size_t)n, f);
    fclose(f);
    if (got != (size_t)n) exit(6);
    *n_out = n;
    return data;
}

static double now_seconds(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

int main(int argc, char **argv) {
    const char *csv_path = "benchmarks/csvagg/data/orders.csv";
    const char *scope = "full";
    for (int a = 1; a < argc; a++) {
        if (strcmp(argv[a], "--csv") == 0 && a + 1 < argc) csv_path = argv[++a];
        else if (strcmp(argv[a], "--scope") == 0 && a + 1 < argc) scope = argv[++a];
    }
    if (strcmp(scope, "full") != 0 && strcmp(scope, "scan") != 0) {
        fprintf(stderr, "--scope must be full or scan\n");
        return 2;
    }

    long n = 0;
    unsigned char *data = NULL;
    if (strcmp(scope, "scan") == 0) data = load_file(csv_path, &n);

    double start = now_seconds();
    if (strcmp(scope, "full") == 0) data = load_file(csv_path, &n);

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

    double elapsed = now_seconds() - start;
    printf("SCOPE: %s\n", scope);
    printf("TIME_SECONDS: %.9f\n", elapsed);
    printf("CHECKSUM: %lld:%lld:%lld:%lld:%lld\n",
           total_rows, order_id_bytes_total, category_bytes_total,
           quantity_bytes_total, price_bytes_total);
    free(data);
    return 0;
}
