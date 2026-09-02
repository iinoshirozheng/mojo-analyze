use std::collections::HashMap;
use std::env;
use std::fs;
use std::time::Instant;

fn parse_csv_arg() -> String {
    let args: Vec<String> = env::args().collect();
    let mut i = 1;
    while i < args.len() {
        if args[i] == "--csv" && i + 1 < args.len() {
            return args[i + 1].clone();
        }
        i += 1;
    }
    "benchmarks/csvagg/data/orders.csv".to_string()
}

fn main() {
    let csv_path = parse_csv_arg();

    let start = Instant::now();

    let data = fs::read_to_string(&csv_path).expect("failed to read csv");
    let mut lines = data.lines();
    lines.next(); // header

    let mut revenue_by_category: HashMap<&str, i64> = HashMap::new();
    let mut total_rows: u64 = 0;

    for line in lines {
        if line.is_empty() {
            continue;
        }
        let mut fields = line.split(',');
        let _order_id = fields.next().unwrap();
        let category = fields.next().unwrap();
        let quantity: i64 = fields.next().unwrap().parse().unwrap();
        let price_cents: i64 = fields.next().unwrap().parse().unwrap();

        *revenue_by_category.entry(category).or_insert(0) += quantity * price_cents;
        total_rows += 1;
    }

    let unique_categories = revenue_by_category.len();

    let mut top: Option<(&str, i64)> = None;
    for (&category, &revenue) in revenue_by_category.iter() {
        top = match top {
            None => Some((category, revenue)),
            Some((best_cat, best_rev)) => {
                if revenue > best_rev || (revenue == best_rev && category < best_cat) {
                    Some((category, revenue))
                } else {
                    Some((best_cat, best_rev))
                }
            }
        };
    }

    let elapsed = start.elapsed().as_secs_f64();
    let (top_category, top_revenue) = top.expect("csv had no rows");

    println!("TIME_SECONDS: {}", elapsed);
    println!(
        "CHECKSUM: {}:{}:{}:{}",
        total_rows, unique_categories, top_category, top_revenue
    );
}
