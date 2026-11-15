# Lab 03.6 — solution notes

## Why the main program deadlocks and how `ordered` fixes it

All four Coffman conditions hold in `hang` mode: each mutex is exclusive, each thread holds one account lock while waiting for the other, a `pthread_mutex` cannot be taken away, and the two waits form a cycle (T1: A→B, T2: B→A). `ordered` breaks **circular wait**: every thread locks the lower address first, so all edges in the lock-order graph point the same way and no cycle can form.

## Extension: Dining Philosophers (`philosophers.c`)

```bash
gcc -Wall -Wextra -O2 -pthread solution/philosophers.c -o philosophers
./philosophers naive 3
./philosophers ordered 3
./philosophers waiter 3
```

Captured on aos-lab, 2026-11-15:

```
mode=naive   meals: 0 0 0 0 0 total=0
DEADLOCK: 5 philosophers still blocked after stop
mode=ordered meals: 120340 662463 7500632 22611780 68901 total=30964116
all philosophers left the table
mode=waiter  meals: 3667026 3385946 3455134 3514889 3531025 total=17554020
all philosophers left the table
```

| Mode | Which Coffman condition is broken | Observed |
|---|---|---|
| `naive` | none: everyone holds the left fork and waits for the right one (circular wait over 5 forks) | 0 meals, all 5 blocked forever |
| `ordered` | circular wait: philosopher 4 takes fork 0 before fork 4 | no deadlock, but **very unfair**: 22.6 M vs 69 k meals. Ordering prevents deadlock, not starvation |
| `waiter` | circular wait at run time: a counting semaphore (`N-1 = 4` seats) guarantees at least one seated philosopher can get both forks | no deadlock and fair (3.4–3.7 M each), at the cost of one more synchronization per meal |

TSan check (captured on aos-lab, 2026-11-15; `setarch x86_64 -R` needed on this VM):

```
$ gcc -Wall -Wextra -O1 -g -fsanitize=thread -pthread solution/philosophers.c -o ph-tsan
$ setarch x86_64 -R ./ph-tsan ordered 2 2>&1 | grep -E "WARNING|mode=|left"
mode=ordered meals: 12155 31665 198939 828550 6411 total=1077720
all philosophers left the table
$ setarch x86_64 -R ./ph-tsan waiter 2 2>&1 | grep -E "WARNING|mode=|left"
WARNING: ThreadSanitizer: lock-order-inversion (potential deadlock) (pid=29796)
mode=waiter  meals: 114731 95765 104928 114631 112794 total=542849
all philosophers left the table
$ setarch x86_64 -R timeout 30 ./ph-tsan naive 2 2>&1 | grep -E "WARNING|mode=|DEADLOCK"
mode=naive   meals: 0 0 0 0 0 total=0
DEADLOCK: 5 philosophers still blocked after stop
```

Two lessons hide in this output:

- **`waiter` is TSan-unclean although it can never deadlock.** The fork-order graph still contains the cycle 0→1→2→3→4→0; the semaphore only guarantees the cycle is never *closed at run time*. TSan (like lockdep) checks lock order, not the extra invariant, so it reports a potential deadlock. To pass the "TSan-clean" requirement, combine both fixes or annotate. `ordered` is clean because its graph is acyclic.
- **`naive` produced no TSan report**: every philosopher took its first fork and blocked on the second before *any* thread completed a second acquisition, so no "acquired B while holding A" edge was ever recorded. Lock-order checkers learn from acquisitions that succeed; run the code in a mode that completes (e.g. one philosopher at a time) to get the report before it hangs.
