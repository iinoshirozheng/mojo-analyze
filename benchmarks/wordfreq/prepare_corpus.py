"""Generate a synthetic text corpus for the word-frequency benchmark.

There is no internet access in this environment, so this does NOT download a
real book. Instead it deterministically samples ~15M word tokens from a
hardcoded vocabulary of common English words, weighted by a Zipfian
(power-law) distribution so the resulting frequency profile looks like real
text (a handful of very common words, a long tail of rare ones) without being
copied from any actual source. Fully reproducible: fixed seed, same output
every run. This script is a one-time setup step and is NOT part of the timed
benchmark.
"""

import random
from pathlib import Path

import numpy as np

SEED = 42
N_TOKENS = 15_000_000
SENTENCE_LEN_MIN = 6
SENTENCE_LEN_MAX = 16
WRAP_COLUMNS = 100
PARAGRAPH_EVERY_N_SENTENCES = 12

_RAW_VOCAB = """
the of and to in a is that for it as was with be by on not he i this are or
his from at which but have an they you one all their there we can if will
would when who so no out up into than then them these some her could said
each other more most been do any our its over also after use two how work
first well way even new want because give day most us life world water room
mother area money story fact month book hand part place case week company
system program question during without again small large next early young
important few public bad same able house year child boy girl man woman
family group problem hand fact eye friend father community door body
information back parent office country app group question government
number night point home car city name business power line end member law
car city school state student idea kind head house service side art past
remain speak read allow add spend grow open walk win offer teach might
seem field local last stand million song data process teacher hard reach
turn form high move student learn area mean call try ask need feel become
leave put mean keep let begin help talk hold play run drive break bring
sense understand watch build spend fall cut light hair land continue
without along following across behind plan far result set free draw
figure million short east north south west almost enough directly
paper industry once level effort building nation street image itself
success value picture almost minor stay reduce cost strategy issue
maybe policy nature research effect research figure race choose
foot boat basket dinner sport garden season ocean forest mountain river
lake island desert valley cloud storm rain snow wind fire ice stone metal
glass wood paper cotton silk wool leather plastic rubber cloth thread
needle thread machine engine wheel bicycle train plane ship boat truck
bridge tunnel road highway street avenue path trail forest jungle desert
""".split()
# de-dup while preserving order (harmless if duplicates slip in above)
VOCAB = list(dict.fromkeys(w.lower() for w in _RAW_VOCAB))


def build_text(n_tokens: int) -> str:
    rng = np.random.default_rng(SEED)
    ranks = np.arange(1, len(VOCAB) + 1, dtype=np.float64)
    weights = 1.0 / ranks
    weights /= weights.sum()
    indices = rng.choice(len(VOCAB), size=n_tokens, p=weights)
    words = [VOCAB[i] for i in indices]

    r = random.Random(SEED)
    lines: list[str] = []
    line_words: list[str] = []
    line_len = 0
    sentences_in_para = 0
    i = 0
    while i < len(words):
        sent_len = r.randint(SENTENCE_LEN_MIN, SENTENCE_LEN_MAX)
        sent_words = words[i : i + sent_len]
        if not sent_words:
            break
        sent_words[0] = sent_words[0].capitalize()
        sentence = " ".join(sent_words) + ("," if r.random() < 0.15 else ".")
        i += sent_len

        for tok_idx, tok in enumerate(sentence.split(" ")):
            piece = tok if line_len == 0 else " " + tok
            if line_len + len(piece) > WRAP_COLUMNS and line_len > 0:
                lines.append(" ".join(line_words))
                line_words = []
                line_len = 0
                piece = tok
            line_words.append(tok)
            line_len += len(piece)

        sentences_in_para += 1
        if sentences_in_para >= PARAGRAPH_EVERY_N_SENTENCES:
            if line_words:
                lines.append(" ".join(line_words))
                line_words = []
                line_len = 0
            lines.append("")
            sentences_in_para = 0

    if line_words:
        lines.append(" ".join(line_words))

    return "\n".join(lines) + "\n"


def main() -> None:
    out_path = Path(__file__).parent / "data" / "corpus.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = build_text(N_TOKENS)
    out_path.write_text(text, encoding="utf-8")
    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"vocab_size={len(VOCAB)} tokens={N_TOKENS} bytes={out_path.stat().st_size} ({size_mb:.1f} MiB)")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
