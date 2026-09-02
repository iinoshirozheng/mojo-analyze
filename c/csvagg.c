// Compile: clang -O3 -o dist/csvagg-c c/csvagg.c
// Byte-span open-addressing hash table keyed by the category field's raw
// bytes -- no per-row allocation, same technique csvagg.mojo/wordfreq.c use.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define CAPACITY 1024
#define MASK (CAPACITY - 1)

static int slot_used[CAPACITY];
static unsigned long long slot_hash[CAPACITY];
static long slot_start[CAPACITY];
static long slot_end[CAPACITY];
static long long slot_revenue[CAPACITY];

int main(int argc, char **argv) {
    const char *csv_path = "benchmarks/csvagg/data/orders.csv";
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--csv") == 0 && i + 1 < argc) {
            csv_path = argv[++i];
        }
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

    memset(slot_used, 0, sizeof(slot_used));
    long long total_rows = 0;

    long i = 0;
    while (i < n && data[i] != '\n') i++;
    i++;

    while (i < n) {
        while (i < n && data[i] != ',') i++;
        i++;

        long cat_start = i;
        while (i < n && data[i] != ',') i++;
        long cat_end = i;
        i++;

        long long quantity = 0;
        while (i < n && data[i] != ',') {
            quantity = quantity * 10 + (data[i] - '0');
            i++;
        }
        i++;

        long long price_cents = 0;
        while (i < n && data[i] != ',' && data[i] != '\n') {
            price_cents = price_cents * 10 + (data[i] - '0');
            i++;
        }
        while (i < n && data[i] != '\n') i++;
        i++;

        long long revenue = quantity * price_cents;
        long span_len = cat_end - cat_start;

        unsigned long long h = 14695981039346656037ULL;
        for (long k = cat_start; k < cat_end; k++) {
            h ^= (unsigned long long)data[k];
            h *= 1099511628211ULL;
        }

        long slot = (long)(h & MASK);
        while (1) {
            if (!slot_used[slot]) {
                slot_used[slot] = 1;
                slot_hash[slot] = h;
                slot_start[slot] = cat_start;
                slot_end[slot] = cat_end;
                slot_revenue[slot] = 0;
                break;
            }
            int matches = 0;
            if (slot_hash[slot] == h && (slot_end[slot] - slot_start[slot]) == span_len) {
                matches = (memcmp(data + slot_start[slot], data + cat_start, (size_t)span_len) == 0);
            }
            if (matches) break;
            slot = (slot + 1) & MASK;
        }
        slot_revenue[slot] += revenue;
        total_rows++;
    }

    long unique_categories = 0;
    char *top_category = NULL;
    long top_len = 0;
    long long top_revenue = -1;

    for (int s = 0; s < CAPACITY; s++) {
        if (!slot_used[s]) continue;
        unique_categories++;
        long len = slot_end[s] - slot_start[s];
        char *cat = malloc((size_t)len + 1);
        memcpy(cat, data + slot_start[s], (size_t)len);
        cat[len] = '\0';

        int take = 0;
        if (top_category == NULL || slot_revenue[s] > top_revenue) {
            take = 1;
        } else if (slot_revenue[s] == top_revenue) {
            long cmp_len = len < top_len ? len : top_len;
            int cmp = memcmp(cat, top_category, (size_t)cmp_len);
            if (cmp < 0 || (cmp == 0 && len < top_len)) take = 1;
        }
        if (take) {
            free(top_category);
            top_category = cat;
            top_len = len;
            top_revenue = slot_revenue[s];
        } else {
            free(cat);
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;

    printf("TIME_SECONDS: %.9f\n", elapsed);
    printf("CHECKSUM: %lld:%ld:%s:%lld\n", total_rows, unique_categories, top_category, top_revenue);
    return 0;
}
