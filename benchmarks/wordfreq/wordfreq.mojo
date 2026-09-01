from std.sys import argv
from std.time import perf_counter_ns

comptime ASCII_a: UInt8 = 97
comptime ASCII_z: UInt8 = 122
comptime ASCII_A: UInt8 = 65
comptime ASCII_Z: UInt8 = 90
comptime ASCII_0: UInt8 = 48
comptime ASCII_9: UInt8 = 57


def is_alnum_byte(b: UInt8) -> Bool:
    return (
        (b >= ASCII_a and b <= ASCII_z)
        or (b >= ASCII_A and b <= ASCII_Z)
        or (b >= ASCII_0 and b <= ASCII_9)
    )


def lower_byte(b: UInt8) -> UInt8:
    if b >= ASCII_A and b <= ASCII_Z:
        return b + 32
    return b


def parse_corpus_arg() -> String:
    var args = argv()
    var i = 1
    while i < len(args):
        if String(args[i]) == "--corpus" and i + 1 < len(args):
            return String(args[i + 1])
        i += 1
    return "benchmarks/wordfreq/data/corpus.txt"


@fieldwise_init
struct WordCount(Copyable, Movable):
    var word: String
    var count: Int


def comes_before(a: WordCount, b: WordCount) -> Bool:
    if a.count != b.count:
        return a.count > b.count
    return a.word < b.word


def main() raises:
    var corpus_path = parse_corpus_arg()

    var start = perf_counter_ns()

    var text = open(corpus_path, "r").read()
    var data = text.as_bytes()
    var n = len(data)

    var counts = Dict[String, Int]()
    var total_tokens = 0
    var token_bytes = List[UInt8]()

    var idx = 0
    while idx < n:
        var b = data[idx]
        if is_alnum_byte(b):
            token_bytes.append(lower_byte(b))
        else:
            if len(token_bytes) > 0:
                var word = String(unsafe_from_utf8=Span(token_bytes))
                total_tokens += 1
                if word in counts:
                    counts[word] = counts[word] + 1
                else:
                    counts[word] = 1
                token_bytes = List[UInt8]()
        idx += 1

    if len(token_bytes) > 0:
        var word = String(unsafe_from_utf8=Span(token_bytes))
        total_tokens += 1
        if word in counts:
            counts[word] = counts[word] + 1
        else:
            counts[word] = 1

    var entries = List[WordCount]()
    for entry in counts.items():
        entries.append(WordCount(entry.key.copy(), entry.value))

    var m = len(entries)
    var i = 1
    while i < m:
        var current = entries[i].copy()
        var j = i - 1
        while j >= 0 and not comes_before(entries[j], current):
            entries[j + 1] = entries[j].copy()
            j -= 1
        entries[j + 1] = current.copy()
        i += 1

    var elapsed_ns = perf_counter_ns() - start
    var elapsed = Float64(elapsed_ns) / 1_000_000_000.0

    print("Top 20 words:")
    var top_n = 20
    if m < top_n:
        top_n = m
    var k = 0
    while k < top_n:
        print("  " + entries[k].word + ": " + String(entries[k].count))
        k += 1

    print("TIME_SECONDS: " + String(elapsed))
    print(
        "CHECKSUM: "
        + String(total_tokens)
        + ":"
        + String(m)
        + ":"
        + entries[0].word
        + ":"
        + String(entries[0].count)
    )
