// Compile: clang -O3 -o dist/wordfreq-c c/wordfreq.c
// Byte-span open-addressing hash table (FNV-1a, linear probing) keyed by
// (start, end) offsets into the mmap'd/read corpus buffer -- no per-token
// allocation, same technique benchmarks/wordfreq/wordfreq.mojo uses.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define CAPACITY 8192
#define MASK (CAPACITY - 1)

static int is_alnum_byte(unsigned char b) {
    return (b >= 'a' && b <= 'z') || (b >= 'A' && b <= 'Z') || (b >= '0' && b <= '9');
}
static unsigned char lower_byte(unsigned char b) {
    if (b >= 'A' && b <= 'Z') return (unsigned char)(b + 32);
    return b;
}

static int slot_used[CAPACITY];
static unsigned long long slot_hash[CAPACITY];
static long slot_start[CAPACITY];
static long slot_end[CAPACITY];
static long long slot_count[CAPACITY];

int main(int argc, char **argv) {
    const char *corpus_path = "benchmarks/wordfreq/data/corpus.txt";
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--corpus") == 0 && i + 1 < argc) {
            corpus_path = argv[++i];
        }
    }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    FILE *f = fopen(corpus_path, "rb");
    if (!f) { fprintf(stderr, "cannot open %s\n", corpus_path); return 1; }
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    unsigned char *data = malloc((size_t)n);
    fread(data, 1, (size_t)n, f);
    fclose(f);

    memset(slot_used, 0, sizeof(slot_used));
    long long total_tokens = 0;
    long token_start = -1;

    for (long idx = 0; idx <= n; idx++) {
        int at_boundary = 1;
        if (idx < n && is_alnum_byte(data[idx])) at_boundary = 0;

        if (at_boundary) {
            if (token_start >= 0) {
                long tok_start = token_start, tok_end = idx;
                long span_len = tok_end - tok_start;

                unsigned long long h = 14695981039346656037ULL;
                for (long k = tok_start; k < tok_end; k++) {
                    h ^= (unsigned long long)lower_byte(data[k]);
                    h *= 1099511628211ULL;
                }

                long slot = (long)(h & MASK);
                while (1) {
                    if (!slot_used[slot]) {
                        slot_used[slot] = 1;
                        slot_hash[slot] = h;
                        slot_start[slot] = tok_start;
                        slot_end[slot] = tok_end;
                        slot_count[slot] = 0;
                        break;
                    }
                    int matches = 0;
                    if (slot_hash[slot] == h && (slot_end[slot] - slot_start[slot]) == span_len) {
                        matches = 1;
                        for (long j = 0; j < span_len; j++) {
                            if (lower_byte(data[slot_start[slot] + j]) != lower_byte(data[tok_start + j])) {
                                matches = 0;
                                break;
                            }
                        }
                    }
                    if (matches) break;
                    slot = (slot + 1) & MASK;
                }
                slot_count[slot]++;
                total_tokens++;
                token_start = -1;
            }
        } else if (token_start < 0) {
            token_start = idx;
        }
    }

    long unique_words = 0;
    char *top_word = NULL;
    long top_word_len = 0;
    long long top_count = -1;

    for (int s = 0; s < CAPACITY; s++) {
        if (!slot_used[s]) continue;
        unique_words++;
        long len = slot_end[s] - slot_start[s];
        char *word = malloc((size_t)len + 1);
        for (long j = 0; j < len; j++) word[j] = (char)lower_byte(data[slot_start[s] + j]);
        word[len] = '\0';

        int take = 0;
        if (top_word == NULL || slot_count[s] > top_count) {
            take = 1;
        } else if (slot_count[s] == top_count) {
            long cmp_len = len < top_word_len ? len : top_word_len;
            int cmp = memcmp(word, top_word, (size_t)cmp_len);
            if (cmp < 0 || (cmp == 0 && len < top_word_len)) take = 1;
        }
        if (take) {
            free(top_word);
            top_word = word;
            top_word_len = len;
            top_count = slot_count[s];
        } else {
            free(word);
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) / 1e9;

    printf("TIME_SECONDS: %.9f\n", elapsed);
    printf("CHECKSUM: %lld:%ld:%s:%lld\n", total_tokens, unique_words, top_word, top_count);
    return 0;
}
