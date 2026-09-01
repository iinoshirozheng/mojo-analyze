"""Word-frequency benchmark: pure Python, manual dict (no collections.Counter)."""

import argparse
import re
import time

TOKEN_RE = re.compile(r"[^A-Za-z0-9]+")


def run(corpus_path: str) -> tuple[float, int, int, str, int, list[tuple[str, int]]]:
    start = time.perf_counter()

    with open(corpus_path, "r", encoding="utf-8") as f:
        text = f.read()

    counts: dict[str, int] = {}
    total_tokens = 0
    for word in TOKEN_RE.split(text.lower()):
        if not word:
            continue
        total_tokens += 1
        counts[word] = counts.get(word, 0) + 1

    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    top20 = ranked[:20]
    top_word, top_count = ranked[0]

    elapsed = time.perf_counter() - start
    return elapsed, total_tokens, len(counts), top_word, top_count, top20


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="benchmarks/wordfreq/data/corpus.txt")
    args = parser.parse_args()

    elapsed, total_tokens, unique_words, top_word, top_count, top20 = run(args.corpus)

    print("Top 20 words:")
    for word, count in top20:
        print(f"  {word}: {count}")

    print(f"TIME_SECONDS: {elapsed:.6f}")
    print(f"CHECKSUM: {total_tokens}:{unique_words}:{top_word}:{top_count}")


if __name__ == "__main__":
    main()
