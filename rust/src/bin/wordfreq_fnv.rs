use std::collections::HashMap;
use std::env;
use std::fs;
use std::hash::{BuildHasherDefault, Hasher};
use std::time::Instant;

struct Fnv1a64(u64);

impl Default for Fnv1a64 {
    fn default() -> Self {
        Self(0xcbf29ce484222325u64)
    }
}

impl Hasher for Fnv1a64 {
    fn write(&mut self, bytes: &[u8]) {
        for &b in bytes {
            self.0 ^= b as u64;
            self.0 = self.0.wrapping_mul(0x100000001b3);
        }
    }

    fn finish(&self) -> u64 {
        self.0
    }
}

type FnvBuildHasher = BuildHasherDefault<Fnv1a64>;

fn parse_corpus_arg() -> String {
    let args: Vec<String> = env::args().collect();
    let mut i = 1;
    while i < args.len() {
        if args[i] == "--corpus" && i + 1 < args.len() {
            return args[i + 1].clone();
        }
        i += 1;
    }
    "benchmarks/wordfreq/data/corpus.txt".to_string()
}

fn is_alnum(b: u8) -> bool {
    (b'a'..=b'z').contains(&b) || (b'A'..=b'Z').contains(&b) || (b'0'..=b'9').contains(&b)
}

fn lower(b: u8) -> u8 {
    if (b'A'..=b'Z').contains(&b) {
        b + 32
    } else {
        b
    }
}

fn main() {
    let corpus_path = parse_corpus_arg();

    let start = Instant::now();

    let data = fs::read(&corpus_path).expect("failed to read corpus");

    // Deliberately preserve Category C's existing owned Vec<u8> key strategy.
    // This experiment changes only the HashMap hasher.
    let mut counts: HashMap<Vec<u8>, u64, FnvBuildHasher> =
        HashMap::with_hasher(FnvBuildHasher::default());
    let mut total_tokens: u64 = 0;
    let mut token: Vec<u8> = Vec::new();

    for &b in data.iter() {
        if is_alnum(b) {
            token.push(lower(b));
        } else if !token.is_empty() {
            total_tokens += 1;
            *counts.entry(std::mem::take(&mut token)).or_insert(0) += 1;
        }
    }
    if !token.is_empty() {
        total_tokens += 1;
        *counts.entry(token).or_insert(0) += 1;
    }

    let unique_words = counts.len();

    let mut top: Option<(&Vec<u8>, &u64)> = None;
    for (word, count) in counts.iter() {
        top = match top {
            None => Some((word, count)),
            Some((best_word, best_count)) => {
                if count > best_count || (count == best_count && word < best_word) {
                    Some((word, count))
                } else {
                    Some((best_word, best_count))
                }
            }
        };
    }

    let elapsed = start.elapsed().as_secs_f64();

    let (top_word, top_count) = top.expect("corpus had no tokens");
    let top_word_str = String::from_utf8_lossy(top_word);

    println!("TIME_SECONDS: {}", elapsed);
    println!(
        "CHECKSUM: {}:{}:{}:{}",
        total_tokens, unique_words, top_word_str, top_count
    );
}
