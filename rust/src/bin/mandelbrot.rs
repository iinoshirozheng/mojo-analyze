use std::env;
use std::time::Instant;

const RE_MIN: f64 = -2.0;
const RE_MAX: f64 = 1.0;
const IM_MIN: f64 = -1.5;
const IM_MAX: f64 = 1.5;

fn parse_args() -> (i64, i64, i64) {
    let args: Vec<String> = env::args().collect();
    let mut width: i64 = 800;
    let mut height: i64 = 600;
    let mut max_iter: i64 = 500;
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--width" if i + 1 < args.len() => {
                width = args[i + 1].parse().unwrap();
                i += 2;
            }
            "--height" if i + 1 < args.len() => {
                height = args[i + 1].parse().unwrap();
                i += 2;
            }
            "--max-iter" if i + 1 < args.len() => {
                max_iter = args[i + 1].parse().unwrap();
                i += 2;
            }
            _ => {
                i += 1;
            }
        }
    }
    (width, height, max_iter)
}

fn main() {
    let (width, height, max_iter) = parse_args();

    let start = Instant::now();

    let w_div = if width - 1 < 1 { 1 } else { width - 1 };
    let h_div = if height - 1 < 1 { 1 } else { height - 1 };
    let dre = (RE_MAX - RE_MIN) / (w_div as f64);
    let dim = (IM_MAX - IM_MIN) / (h_div as f64);

    let mut total: i64 = 0;
    for y in 0..height {
        let im = IM_MAX - dim * (y as f64);
        for x in 0..width {
            let re = RE_MIN + dre * (x as f64);
            let mut zr: f64 = 0.0;
            let mut zi: f64 = 0.0;
            let mut cnt: i64 = 0;
            while cnt < max_iter && zr * zr + zi * zi <= 4.0 {
                let new_zr = zr * zr - zi * zi + re;
                zi = 2.0 * zr * zi + im;
                zr = new_zr;
                cnt += 1;
            }
            total += cnt;
        }
    }

    let elapsed = start.elapsed().as_secs_f64();
    println!("TIME_SECONDS: {}", elapsed);
    println!("CHECKSUM: {}", total);
}
