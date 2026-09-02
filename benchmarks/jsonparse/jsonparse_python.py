"""JSON parsing benchmark -- pure Python, hand-rolled recursive-descent
parser (no `json` module). The "naive" role, parallel to the manual
CSV/dict variants elsewhere in this repo. Only handles what this benchmark's
data actually contains (objects, arrays, strings with \\" and \\\\ escapes,
non-negative integers) -- not a general-purpose JSON library.
"""

import argparse
import time


class Parser:
    __slots__ = ("s", "i", "n")

    def __init__(self, s):
        self.s = s
        self.i = 0
        self.n = len(s)

    def skip_ws(self):
        s, i, n = self.s, self.i, self.n
        while i < n and s[i] in " \t\n\r":
            i += 1
        self.i = i

    def parse_value(self):
        self.skip_ws()
        c = self.s[self.i]
        if c == "{":
            return self.parse_object()
        if c == "[":
            return self.parse_array()
        if c == '"':
            return self.parse_string()
        return self.parse_number()

    def parse_object(self):
        self.i += 1  # {
        obj = {}
        self.skip_ws()
        if self.s[self.i] == "}":
            self.i += 1
            return obj
        while True:
            self.skip_ws()
            key = self.parse_string()
            self.skip_ws()
            self.i += 1  # :
            val = self.parse_value()
            obj[key] = val
            self.skip_ws()
            c = self.s[self.i]
            self.i += 1
            if c == "}":
                return obj
            # else c == ',', continue

    def parse_array(self):
        self.i += 1  # [
        arr = []
        self.skip_ws()
        if self.s[self.i] == "]":
            self.i += 1
            return arr
        while True:
            val = self.parse_value()
            arr.append(val)
            self.skip_ws()
            c = self.s[self.i]
            self.i += 1
            if c == "]":
                return arr
            # else c == ',', continue

    def parse_string(self):
        s = self.s
        i = self.i + 1  # skip opening "
        start = i
        n = self.n
        has_escape = False
        while s[i] != '"':
            if s[i] == "\\":
                has_escape = True
                i += 2
            else:
                i += 1
        raw = s[start:i]
        self.i = i + 1  # skip closing "
        if not has_escape:
            return raw
        # Unescape \" and \\ -- the only two escapes this dataset generates.
        out = []
        j = 0
        L = len(raw)
        while j < L:
            ch = raw[j]
            if ch == "\\" and j + 1 < L:
                nxt = raw[j + 1]
                if nxt == '"':
                    out.append('"')
                    j += 2
                    continue
                if nxt == "\\":
                    out.append("\\")
                    j += 2
                    continue
            out.append(ch)
            j += 1
        return "".join(out)

    def parse_number(self):
        s = self.s
        i = self.i
        start = i
        n = self.n
        if s[i] == "-":
            i += 1
        while i < n and s[i].isdigit():
            i += 1
        self.i = i
        return int(s[start:i])


def main():
    parser_args = argparse.ArgumentParser()
    parser_args.add_argument("--json", default="benchmarks/jsonparse/data/events.json")
    args = parser_args.parse_args()

    start = time.perf_counter()

    with open(args.json, "r") as f:
        text = f.read()

    events = Parser(text).parse_value()

    totals = {}
    for ev in events:
        t = ev["type"]
        totals[t] = totals.get(t, 0) + ev["amount_cents"]

    total_events = len(events)
    unique_types = len(totals)
    top_type, top_revenue = None, -1
    for t, revenue in totals.items():
        if revenue > top_revenue or (revenue == top_revenue and t < top_type):
            top_type, top_revenue = t, revenue

    elapsed = time.perf_counter() - start

    print(f"TIME_SECONDS: {elapsed}")
    print(f"CHECKSUM: {total_events}:{unique_types}:{top_type}:{top_revenue}")


if __name__ == "__main__":
    main()
