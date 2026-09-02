// Compile: clang -O3 -o dist/jsonparse-c c/jsonparse.c
// Hand-rolled scanning parser, standard library only -- same approach as
// jsonparse.mojo: walk the array of event objects, pull "type" and
// "amount_cents", skip everything else (id, nested user object, tags
// array) via a generic skip_value() that respects real JSON nesting/
// escaping rather than special-casing this exact schema.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define CAPACITY 512
#define MASK (CAPACITY - 1)

static int slot_used[CAPACITY];
static unsigned long long slot_hash[CAPACITY];
static long slot_start[CAPACITY];
static long slot_end[CAPACITY];
static long long slot_revenue[CAPACITY];

static long skip_ws(const unsigned char *d, long i) {
    while (d[i] == ' ' || d[i] == '\t' || d[i] == '\n' || d[i] == '\r') i++;
    return i;
}

static long skip_string(const unsigned char *d, long i) {
    i++;  // opening "
    while (d[i] != '"') {
        if (d[i] == '\\') i += 2; else i++;
    }
    return i + 1;
}

static long skip_value(const unsigned char *d, long i) {
    i = skip_ws(d, i);
    unsigned char c = d[i];
    if (c == '"') return skip_string(d, i);
    if (c == '{' || c == '[') {
        unsigned char open_c = c, close_c = (c == '{') ? '}' : ']';
        int depth = 1;
        i++;
        while (depth > 0) {
            unsigned char ch = d[i];
            if (ch == '"') { i = skip_string(d, i); continue; }
            else if (ch == open_c) depth++;
            else if (ch == close_c) depth--;
            i++;
        }
        return i;
    }
    if (d[i] == '-') i++;
    while (d[i] >= '0' && d[i] <= '9') i++;
    return i;
}

int main(int argc, char **argv) {
    const char *json_path = "benchmarks/jsonparse/data/events.json";
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--json") == 0 && i + 1 < argc) {
            json_path = argv[++i];
        }
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    FILE *f = fopen(json_path, "rb");
    if (!f) { fprintf(stderr, "cannot open %s\n", json_path); return 1; }
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    unsigned char *data = malloc((size_t)n);
    fread(data, 1, (size_t)n, f);
    fclose(f);

    memset(slot_used, 0, sizeof(slot_used));
    long long total_events = 0;

    long i = skip_ws(data, 0);
    i++;  // '['
    i = skip_ws(data, i);

    if (data[i] != ']') {
        while (1) {
            i = skip_ws(data, i);
            i++;  // '{'
            long type_start = -1, type_end = -1;
            long long amount_cents = 0;

            i = skip_ws(data, i);
            while (data[i] != '}') {
                long key_start = i + 1;
                long key_end_incl = skip_string(data, i);
                long key_end = key_end_incl - 1;
                long vpos = skip_ws(data, key_end_incl);
                vpos++;  // ':'
                vpos = skip_ws(data, vpos);

                long klen = key_end - key_start;
                if (klen == 4 && memcmp(data + key_start, "type", 4) == 0) {
                    type_start = vpos + 1;
                    long vend = skip_string(data, vpos);
                    type_end = vend - 1;
                    i = vend;
                } else if (klen == 12 && memcmp(data + key_start, "amount_cents", 12) == 0) {
                    long num_start = vpos;
                    long vend = skip_value(data, vpos);
                    long long val = 0;
                    int neg = 0;
                    long k = num_start;
                    if (data[k] == '-') { neg = 1; k++; }
                    while (k < vend) { val = val * 10 + (data[k] - '0'); k++; }
                    amount_cents = neg ? -val : val;
                    i = vend;
                } else {
                    i = skip_value(data, vpos);
                }

                i = skip_ws(data, i);
                if (data[i] == ',') {
                    i++;
                    i = skip_ws(data, i);
                }
            }
            i++;  // '}'

            long span_len = type_end - type_start;
            unsigned long long h = 14695981039346656037ULL;
            for (long k = type_start; k < type_end; k++) {
                h ^= (unsigned long long)data[k];
                h *= 1099511628211ULL;
            }
            long slot = (long)(h & MASK);
            while (1) {
                if (!slot_used[slot]) {
                    slot_used[slot] = 1;
                    slot_hash[slot] = h;
                    slot_start[slot] = type_start;
                    slot_end[slot] = type_end;
                    slot_revenue[slot] = 0;
                    break;
                }
                int matches = 0;
                if (slot_hash[slot] == h && (slot_end[slot] - slot_start[slot]) == span_len) {
                    matches = (memcmp(data + slot_start[slot], data + type_start, (size_t)span_len) == 0);
                }
                if (matches) break;
                slot = (slot + 1) & MASK;
            }
            slot_revenue[slot] += amount_cents;
            total_events++;

            i = skip_ws(data, i);
            if (data[i] == ',') {
                i++;
            } else {
                i++;  // ']'
                break;
            }
        }
    }

    long unique_types = 0;
    char *top_type = NULL;
    long top_len = 0;
    long long top_revenue = -1;

    for (int s = 0; s < CAPACITY; s++) {
        if (!slot_used[s]) continue;
        unique_types++;
        long len = slot_end[s] - slot_start[s];
        char *t = malloc((size_t)len + 1);
        memcpy(t, data + slot_start[s], (size_t)len);
        t[len] = '\0';

        int take = 0;
        if (top_type == NULL || slot_revenue[s] > top_revenue) {
            take = 1;
        } else if (slot_revenue[s] == top_revenue) {
            long cmp_len = len < top_len ? len : top_len;
            int cmp = memcmp(t, top_type, (size_t)cmp_len);
            if (cmp < 0 || (cmp == 0 && len < top_len)) take = 1;
        }
        if (take) {
            free(top_type);
            top_type = t;
            top_len = len;
            top_revenue = slot_revenue[s];
        } else {
            free(t);
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;

    printf("TIME_SECONDS: %.9f\n", elapsed);
    printf("CHECKSUM: %lld:%ld:%s:%lld\n", total_events, unique_types, top_type, top_revenue);
    return 0;
}
