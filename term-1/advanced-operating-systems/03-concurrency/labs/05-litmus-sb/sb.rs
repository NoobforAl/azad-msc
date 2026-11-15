// sb.rs: store-buffering (SB) litmus test in Rust (std only, no crates).
//   T0: x = 1; r0 = y;        T1: y = 1; r1 = x;
// Modes:
//   relaxed : Ordering::Relaxed + compiler_fence(SeqCst)  -> hardware may reorder
//   fence   : Ordering::Relaxed + fence(SeqCst)           -> x86: full barrier (lock or / mfence)
//   seqcst  : Ordering::SeqCst store and load
// Build: rustc -O sb.rs -o sb_rs
// Run:   ./sb_rs <relaxed|fence|seqcst> <iterations>
use std::env;
use std::sync::atomic::{compiler_fence, fence, AtomicI32, AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread;

#[derive(Clone, Copy, PartialEq)]
enum Mode {
    Relaxed,
    Fence,
    SeqCst,
}

struct Shared {
    x: Vec<AtomicI32>,
    y: Vec<AtomicI32>,
    r0: Vec<AtomicI32>,
    r1: Vec<AtomicI32>,
    bar_count: AtomicUsize,
    bar_sense: AtomicUsize,
}

// Two-thread sense-reversing spin barrier.
fn barrier_wait(s: &Shared, local_sense: &mut usize) {
    *local_sense ^= 1;
    if s.bar_count.fetch_add(1, Ordering::SeqCst) == 1 {
        s.bar_count.store(0, Ordering::SeqCst);
        s.bar_sense.store(*local_sense, Ordering::SeqCst);
    } else {
        while s.bar_sense.load(Ordering::SeqCst) != *local_sense {
            std::hint::spin_loop();
        }
    }
}

fn run(s: Arc<Shared>, me: usize, mode: Mode, iters: usize) {
    let (mine, other, out) = if me == 0 {
        (&s.x, &s.y, &s.r0)
    } else {
        (&s.y, &s.x, &s.r1)
    };
    let mut sense = 0usize;
    for i in 0..iters {
        barrier_wait(&s, &mut sense);
        let v = match mode {
            Mode::Relaxed => {
                mine[i].store(1, Ordering::Relaxed);
                compiler_fence(Ordering::SeqCst); // compiler barrier only
                other[i].load(Ordering::Relaxed)
            }
            Mode::Fence => {
                mine[i].store(1, Ordering::Relaxed);
                fence(Ordering::SeqCst); // full hardware barrier
                other[i].load(Ordering::Relaxed)
            }
            Mode::SeqCst => {
                mine[i].store(1, Ordering::SeqCst);
                other[i].load(Ordering::SeqCst)
            }
        };
        out[i].store(v, Ordering::Relaxed);
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("usage: {} <relaxed|fence|seqcst> <iterations>", args[0]);
        std::process::exit(2);
    }
    let mode = match args[1].as_str() {
        "relaxed" => Mode::Relaxed,
        "fence" => Mode::Fence,
        "seqcst" => Mode::SeqCst,
        _ => {
            eprintln!("bad mode");
            std::process::exit(2);
        }
    };
    let iters: usize = args[2].parse().expect("iterations");
    let mk = |n: usize| (0..n).map(|_| AtomicI32::new(0)).collect::<Vec<_>>();
    let s = Arc::new(Shared {
        x: mk(iters),
        y: mk(iters),
        r0: mk(iters),
        r1: mk(iters),
        bar_count: AtomicUsize::new(0),
        bar_sense: AtomicUsize::new(0),
    });

    let handles: Vec<_> = (0..2)
        .map(|me| {
            let s = Arc::clone(&s);
            thread::spawn(move || run(s, me, mode, iters))
        })
        .collect();
    for h in handles {
        h.join().unwrap();
    }

    let mut hist = [[0u64; 2]; 2];
    for i in 0..iters {
        let a = s.r0[i].load(Ordering::Relaxed) as usize;
        let b = s.r1[i].load(Ordering::Relaxed) as usize;
        hist[a][b] += 1;
    }
    println!("rust mode={:<7} iters={}", args[1], iters);
    println!(
        "  r0=0 r1=0 : {:>9}  ({:.4}%)  <- forbidden under SC",
        hist[0][0],
        100.0 * hist[0][0] as f64 / iters as f64
    );
    println!("  r0=0 r1=1 : {:>9}", hist[0][1]);
    println!("  r0=1 r1=0 : {:>9}", hist[1][0]);
    println!("  r0=1 r1=1 : {:>9}", hist[1][1]);
}
