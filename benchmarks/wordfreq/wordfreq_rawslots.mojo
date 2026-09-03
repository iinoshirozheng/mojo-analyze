from std.sys import argv
from std.time import perf_counter_ns

comptime ASCII_a: UInt8 = 97
comptime ASCII_z: UInt8 = 122
comptime ASCII_A: UInt8 = 65
comptime ASCII_Z: UInt8 = 90
comptime ASCII_0: UInt8 = 48
comptime ASCII_9: UInt8 = 57
comptime FNV_OFFSET: UInt64 = 14695981039346656037
comptime FNV_PRIME: UInt64 = 1099511628211
comptime CAPACITY = 8192
comptime MASK = CAPACITY - 1


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

    var start_time = perf_counter_ns()

    var text = open(corpus_path, "r").read()
    var data = text.as_bytes()
    var n = len(data)

    # Experiment variant: identical open-addressing table and probing logic to
    # wordfreq.mojo, but the five fixed-capacity slot arrays are raw pointers.
    # This isolates List bounds-check/storage overhead without changing hashing,
    # key representation, corpus parsing, sorting, or checksum semantics.
    var slot_used = alloc[UInt8](CAPACITY)
    var slot_hash = alloc[UInt64](CAPACITY)
    var slot_start = alloc[Int](CAPACITY)
    var slot_end = alloc[Int](CAPACITY)
    var slot_count = alloc[Int](CAPACITY)
    for s in range(CAPACITY):
        slot_used[unsafe_offset=s] = 0

    var total_tokens = 0

    var idx = 0
    var token_start = -1
    while idx <= n:
        var at_boundary = True
        if idx < n:
            if is_alnum_byte(data[idx]):
                at_boundary = False

        if at_boundary:
            if token_start >= 0:
                var tok_start = token_start
                var tok_end = idx
                var span_len = tok_end - tok_start

                var h: UInt64 = FNV_OFFSET
                var i = tok_start
                while i < tok_end:
                    h = h ^ UInt64(lower_byte(data[i]))
                    h = h * FNV_PRIME
                    i += 1

                var slot = Int(h) & MASK
                while True:
                    if slot_used[unsafe_offset=slot] == 0:
                        slot_used[unsafe_offset=slot] = 1
                        slot_hash[unsafe_offset=slot] = h
                        slot_start[unsafe_offset=slot] = tok_start
                        slot_end[unsafe_offset=slot] = tok_end
                        slot_count[unsafe_offset=slot] = 0
                        break

                    var matches = False
                    if (
                        slot_hash[unsafe_offset=slot] == h
                        and (
                            slot_end[unsafe_offset=slot]
                            - slot_start[unsafe_offset=slot]
                        ) == span_len
                    ):
                        matches = True
                        var j = 0
                        while j < span_len:
                            if (
                                lower_byte(
                                    data[slot_start[unsafe_offset=slot] + j]
                                )
                                != lower_byte(data[tok_start + j])
                            ):
                                matches = False
                                break
                            j += 1

                    if matches:
                        break
                    slot = (slot + 1) & MASK

                slot_count[unsafe_offset=slot] = (
                    slot_count[unsafe_offset=slot] + 1
                )
                total_tokens += 1
                token_start = -1
        else:
            if token_start < 0:
                token_start = idx

        idx += 1

    var entries = List[WordCount]()
    var s = 0
    while s < CAPACITY:
        if slot_used[unsafe_offset=s] == 1:
            var buf = List[UInt8]()
            var p = slot_start[unsafe_offset=s]
            while p < slot_end[unsafe_offset=s]:
                buf.append(lower_byte(data[p]))
                p += 1
            var word = String(unsafe_from_utf8=Span(buf))
            entries.append(WordCount(word, slot_count[unsafe_offset=s]))
        s += 1

    var m = len(entries)
    var ii = 1
    while ii < m:
        var current = entries[ii].copy()
        var jj = ii - 1
        while jj >= 0 and not comes_before(entries[jj], current):
            entries[jj + 1] = entries[jj].copy()
            jj -= 1
        entries[jj + 1] = current.copy()
        ii += 1

    var elapsed_ns = perf_counter_ns() - start_time
    var elapsed = Float64(elapsed_ns) / 1_000_000_000.0

    # Keep deallocation outside the timed region, matching the canonical List
    # variant whose destructors run after its timer is stopped.
    slot_used.unsafe_free()
    slot_hash.unsafe_free()
    slot_start.unsafe_free()
    slot_end.unsafe_free()
    slot_count.unsafe_free()

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
