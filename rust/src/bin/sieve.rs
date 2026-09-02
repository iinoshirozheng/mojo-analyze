use std::env;
use std::time::Instant;

fn parse_limit() -> usize {
    let args: Vec<String> = env::args().collect();
    let mut limit: usize = 50_000_000;
    let mut i = 1;
    while i < args.len() {
        if args[i] == "--limit" && i + 1 < args.len() {
            limit = args[i + 1].parse().unwrap();
            i += 2;
        } else {
            i += 1;
        }
    }
    limit
}

fn main() {
    let limit = parse_limit();

    let start = Instant::now();

    let mut is_prime = vec![true; limit + 1];
    is_prime[0] = false;
    if limit >= 1 {
        is_prime[1] = false;
    }

    let mut i = 2usize;
    while i * i <= limit {
        if is_prime[i] {
            let mut j = i * i;
            while j <= limit {
                is_prime[j] = false;
                j += i;
            }
        }
        i += 1;
    }

    let mut count: u64 = 0;
    let mut total: u64 = 0;
    for idx in 2..=limit {
        if is_prime[idx] {
            count += 1;
            total += idx as u64;
        }
    }

    let elapsed = start.elapsed().as_secs_f64();
    let sum_mod = total % 1_000_000_007;

    println!("TIME_SECONDS: {}", elapsed);
    println!("CHECKSUM: {}:{}", count, sum_mod);
}
