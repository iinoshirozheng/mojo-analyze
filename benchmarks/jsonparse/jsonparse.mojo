# Mojo has no JSON stdlib, so this is a small hand-rolled scanning parser --
# not a general-purpose reusable library, just enough to walk this dataset's
# structure (an array of objects, some nested) and pull out the two fields
# the benchmark needs (`type`, `amount_cents`), skipping everything else
# (`id`, the nested `user` object, the `tags` array) via a generic
# skip_value() that still respects JSON's actual nesting/escaping rules
# rather than special-casing this exact schema. Same lesson this repo
# already learned twice (word-freq, CSV agg): no per-event String
# allocation for the `type` field in the hot loop -- byte-span hash table,
# same technique as benchmarks/wordfreq/wordfreq.mojo.
#
# Empirically profiled (see ANALYSIS.md's category-E section) rather than
# left as a guess: `@always_inline` on the five scanning helpers below is a
# real, measured ~20-25% win (confirmed via `mojo build --emit asm` -- zero
# `call` instructions to these functions remain in the compiled binary, so
# this genuinely is full inlining, not a compiler no-op). Raw-pointer
# access (`Pointer[UInt8, _]` instead of `Span[UInt8, _]`) on top of that
# was tested and found NOT to matter here (unlike sieve.mojo/wordfreq.mojo,
# where it was the dominant fix) -- kept anyway for consistency with the
# rest of this repo's "no bounds-checked collection in the hot loop"
# convention, at no measured cost. The hash table itself was also profiled
# out as a candidate cause (removing it entirely saves only ~5-8% of total
# time) -- the scanning loop itself, not the hash table, is where the
# remaining gap to Rust/C lives; seven searchable structural characters and
# a branch per byte is inherently more instruction-dense than a
# whitespace/comma split, and simdjson's whole reason for existing is that
# even well-tuned scalar/branchless JSON parsers (RapidJSON, sajson) still
# spend meaningfully more instructions per byte than a SIMD structural-index
# pass -- see ANALYSIS.md for the full writeup and citations.
from std.sys import argv
from std.time import perf_counter_ns

comptime CAPACITY = 512
comptime MASK = CAPACITY - 1
comptime FNV_OFFSET: UInt64 = 14695981039346656037
comptime FNV_PRIME: UInt64 = 1099511628211


def parse_json_arg() -> String:
    var args = argv()
    var i = 1
    while i < len(args):
        if String(args[i]) == "--json" and i + 1 < len(args):
            return String(args[i + 1])
        i += 1
    return "benchmarks/jsonparse/data/events.json"


@always_inline
def skip_ws(data: Pointer[UInt8, _], n: Int, pos: Int) -> Int:
    var i = pos
    while i < n and (data[unsafe_offset=i] == 32 or data[unsafe_offset=i] == 9 or data[unsafe_offset=i] == 10 or data[unsafe_offset=i] == 13):
        i += 1
    return i


@always_inline
def skip_string(data: Pointer[UInt8, _], pos: Int) -> Int:
    # pos points at the opening '"'.
    var i = pos + 1
    while data[unsafe_offset=i] != 34:  # '"'
        if data[unsafe_offset=i] == 92:  # '\\'
            i += 2
        else:
            i += 1
    return i + 1


@always_inline
def skip_value(data: Pointer[UInt8, _], n: Int, pos: Int) -> Int:
    var i = skip_ws(data, n, pos)
    var c = data[unsafe_offset=i]
    if c == 34:  # '"'
        return skip_string(data, i)
    if c == 123 or c == 91:  # '{' or '['
        var open_c = c
        var close_c: UInt8 = 125 if c == 123 else 93
        var depth = 1
        i += 1
        while depth > 0:
            var ch = data[unsafe_offset=i]
            if ch == 34:
                i = skip_string(data, i)
                continue
            elif ch == open_c:
                depth += 1
            elif ch == close_c:
                depth -= 1
            i += 1
        return i
    # number (int, possibly negative)
    if data[unsafe_offset=i] == 45:  # '-'
        i += 1
    while i < n and data[unsafe_offset=i] >= 48 and data[unsafe_offset=i] <= 57:
        i += 1
    return i


@always_inline
def parse_key(data: Pointer[UInt8, _], n: Int, pos: Int) -> Tuple[Int, Int, Int]:
    # pos points at the opening '"' of a key. Returns (key_start, key_end, pos_after_colon).
    var key_start = pos + 1
    var end = skip_string(data, pos)
    var key_end = end - 1
    var i = skip_ws(data, n, end)
    i += 1  # ':'
    return (key_start, key_end, i)


@always_inline
def key_is(data: Pointer[UInt8, _], start: Int, end: Int, target: StaticString) -> Bool:
    var tb = target.as_bytes()
    if end - start != len(tb):
        return False
    var i = 0
    while i < end - start:
        if data[unsafe_offset=start + i] != tb[i]:
            return False
        i += 1
    return True


def main() raises:
    var json_path = parse_json_arg()

    var start = perf_counter_ns()

    var text = open(json_path, "r").read()
    var n = text.byte_length()
    var data = text.unsafe_ptr()

    var slot_used = List[Bool](length=CAPACITY, fill=False)
    var slot_hash = List[UInt64](length=CAPACITY, fill=0)
    var slot_start = List[Int](length=CAPACITY, fill=0)
    var slot_end = List[Int](length=CAPACITY, fill=0)
    var slot_revenue = List[Int64](length=CAPACITY, fill=0)
    var total_events = 0

    var i = skip_ws(data, n, 0)
    i += 1  # '['
    i = skip_ws(data, n, i)
    if data[unsafe_offset=i] == 93:  # empty array ']'
        i += 1
    else:
        while True:
            i = skip_ws(data, n, i)
            i += 1  # '{'
            var type_start = -1
            var type_end = -1
            var amount_cents: Int64 = 0

            i = skip_ws(data, n, i)
            while data[unsafe_offset=i] != 125:  # '}'
                var kr = parse_key(data, n, i)
                var key_start = kr[0]
                var key_end = kr[1]
                var vpos = skip_ws(data, n, kr[2])

                if key_is(data, key_start, key_end, "type"):
                    type_start = vpos + 1
                    var vend = skip_string(data, vpos)
                    type_end = vend - 1
                    i = vend
                elif key_is(data, key_start, key_end, "amount_cents"):
                    var num_start = vpos
                    var vend = skip_value(data, n, vpos)
                    var val: Int64 = 0
                    var neg = False
                    var k = num_start
                    if data[unsafe_offset=k] == 45:
                        neg = True
                        k += 1
                    while k < vend:
                        val = val * 10 + Int64(data[unsafe_offset=k] - 48)
                        k += 1
                    amount_cents = -val if neg else val
                    i = vend
                else:
                    i = skip_value(data, n, vpos)

                i = skip_ws(data, n, i)
                if data[unsafe_offset=i] == 44:  # ','
                    i += 1
                    i = skip_ws(data, n, i)
            i += 1  # '}'

            # type_start/type_end are always set: every event in this
            # dataset has a "type" field (generator guarantee).
            var span_len = type_end - type_start
            var h: UInt64 = FNV_OFFSET
            var kk = type_start
            while kk < type_end:
                h = h ^ UInt64(data[unsafe_offset=kk])
                h = h * FNV_PRIME
                kk += 1

            var slot = Int(h) & MASK
            while True:
                if not slot_used[slot]:
                    slot_used[slot] = True
                    slot_hash[slot] = h
                    slot_start[slot] = type_start
                    slot_end[slot] = type_end
                    slot_revenue[slot] = 0
                    break
                var matches = False
                if slot_hash[slot] == h and (slot_end[slot] - slot_start[slot]) == span_len:
                    matches = True
                    var j = 0
                    while j < span_len:
                        if data[unsafe_offset=slot_start[slot] + j] != data[unsafe_offset=type_start + j]:
                            matches = False
                            break
                        j += 1
                if matches:
                    break
                slot = (slot + 1) & MASK

            slot_revenue[slot] = slot_revenue[slot] + amount_cents
            total_events += 1

            i = skip_ws(data, n, i)
            if data[unsafe_offset=i] == 44:  # ',' -- another event
                i += 1
            else:
                i += 1  # ']'
                break

    var unique_types = 0
    var top_type = ""
    var top_revenue = Int64(-1)
    var have_top = False
    var s = 0
    while s < CAPACITY:
        if slot_used[s]:
            unique_types += 1
            var rev = slot_revenue[s]
            var buf = List[UInt8]()
            var p = slot_start[s]
            while p < slot_end[s]:
                buf.append(data[unsafe_offset=p])
                p += 1
            var etype = String(unsafe_from_utf8=Span(buf))
            if not have_top or rev > top_revenue or (rev == top_revenue and etype < top_type):
                top_type = etype
                top_revenue = rev
                have_top = True
        s += 1

    var elapsed_ns = perf_counter_ns() - start
    var elapsed = Float64(elapsed_ns) / 1_000_000_000.0

    print("TIME_SECONDS: " + String(elapsed))
    print(
        "CHECKSUM: "
        + String(total_events)
        + ":"
        + String(unique_types)
        + ":"
        + top_type
        + ":"
        + String(top_revenue)
    )
