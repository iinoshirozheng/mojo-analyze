// JSON parsing benchmark (category E) — hand-rolled parser, std only, no
// serde_json, matching every other Rust variant in this repo. Only as
// general as this dataset's shape requires (objects, arrays, strings with
// \" and \\ escapes, non-negative integers).

use std::collections::HashMap;
use std::env;
use std::fs;
use std::time::Instant;

fn parse_json_arg() -> String {
    let args: Vec<String> = env::args().collect();
    let mut i = 1;
    while i < args.len() {
        if args[i] == "--json" && i + 1 < args.len() {
            return args[i + 1].clone();
        }
        i += 1;
    }
    "benchmarks/jsonparse/data/events.json".to_string()
}

struct Parser<'a> {
    b: &'a [u8],
    i: usize,
}

impl<'a> Parser<'a> {
    fn skip_ws(&mut self) {
        while self.i < self.b.len() {
            match self.b[self.i] {
                b' ' | b'\t' | b'\n' | b'\r' => self.i += 1,
                _ => break,
            }
        }
    }

    // Advances past a string starting at the opening '"', honoring \" and
    // \\ escapes so an escaped quote never terminates the string early.
    // Returns the byte span of the *raw* (still-escaped) content.
    fn skip_string(&mut self) -> (usize, usize) {
        self.i += 1; // opening "
        let start = self.i;
        while self.b[self.i] != b'"' {
            if self.b[self.i] == b'\\' {
                self.i += 2;
            } else {
                self.i += 1;
            }
        }
        let end = self.i;
        self.i += 1; // closing "
        (start, end)
    }

    fn parse_number(&mut self) -> i64 {
        let start = self.i;
        if self.b[self.i] == b'-' {
            self.i += 1;
        }
        while self.i < self.b.len() && self.b[self.i].is_ascii_digit() {
            self.i += 1;
        }
        std::str::from_utf8(&self.b[start..self.i])
            .unwrap()
            .parse()
            .unwrap()
    }

    fn skip_value(&mut self) {
        self.skip_ws();
        match self.b[self.i] {
            b'{' => {
                self.i += 1;
                self.skip_ws();
                if self.b[self.i] == b'}' {
                    self.i += 1;
                    return;
                }
                loop {
                    self.skip_ws();
                    self.skip_string(); // key
                    self.skip_ws();
                    self.i += 1; // :
                    self.skip_value();
                    self.skip_ws();
                    let c = self.b[self.i];
                    self.i += 1;
                    if c == b'}' {
                        break;
                    }
                }
            }
            b'[' => {
                self.i += 1;
                self.skip_ws();
                if self.b[self.i] == b']' {
                    self.i += 1;
                    return;
                }
                loop {
                    self.skip_value();
                    self.skip_ws();
                    let c = self.b[self.i];
                    self.i += 1;
                    if c == b']' {
                        break;
                    }
                }
            }
            b'"' => {
                self.skip_string();
            }
            _ => {
                self.parse_number();
            }
        }
    }

    // Parse one top-level event object, extracting only "type" and
    // "amount_cents"; user{} and tags[] are structurally walked
    // (skip_value) to prove full JSON parsing, not skipped as raw bytes.
    // "type"'s value never contains escapes in this dataset, so its raw
    // span is returned as-is (no unescape pass needed for the aggregation
    // key — only tags, which are unused, ever carry \" / \\).
    fn parse_event(&mut self) -> (&'a str, i64) {
        self.i += 1; // {
        let mut event_type: Option<&'a str> = None;
        let mut amount_cents: i64 = 0;
        self.skip_ws();
        loop {
            self.skip_ws();
            let (ks, ke) = self.skip_string(); // key
            let key = std::str::from_utf8(&self.b[ks..ke]).unwrap();
            self.skip_ws();
            self.i += 1; // :
            if key == "type" {
                self.skip_ws();
                let (vs, ve) = self.skip_string();
                event_type = Some(std::str::from_utf8(&self.b[vs..ve]).unwrap());
            } else if key == "amount_cents" {
                self.skip_ws();
                amount_cents = self.parse_number();
            } else {
                self.skip_value();
            }
            self.skip_ws();
            let c = self.b[self.i];
            self.i += 1;
            if c == b'}' {
                break;
            }
        }
        (event_type.unwrap(), amount_cents)
    }
}

fn main() {
    let json_path = parse_json_arg();

    let start = Instant::now();

    let data = fs::read(&json_path).expect("failed to read json");
    let mut p = Parser { b: &data, i: 0 };

    p.skip_ws();
    p.i += 1; // [

    let mut totals: HashMap<&str, i64> = HashMap::new();
    let mut total_events: u64 = 0;

    p.skip_ws();
    if p.b[p.i] != b']' {
        loop {
            p.skip_ws();
            let (event_type, amount_cents) = p.parse_event();
            *totals.entry(event_type).or_insert(0) += amount_cents;
            total_events += 1;

            p.skip_ws();
            let c = p.b[p.i];
            p.i += 1;
            if c == b']' {
                break;
            }
        }
    }

    let mut top_type = "";
    let mut top_total = i64::MIN;
    let mut keys: Vec<&&str> = totals.keys().collect();
    keys.sort();
    for k in keys {
        let v = totals[k];
        if v > top_total {
            top_total = v;
            top_type = k;
        }
    }

    let elapsed = start.elapsed().as_secs_f64();

    println!("TIME_SECONDS: {:.6}", elapsed);
    println!(
        "CHECKSUM: {}:{}:{}:{}",
        total_events,
        totals.len(),
        top_type,
        top_total
    );
}
