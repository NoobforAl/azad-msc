# 05 — Fault tolerance basics: failure models, replication, quorums, consensus preview

> Module 06 · Distributed OS & Virtualization · Pins: Linux **v6.18.63**, OpenBSD **`8cada8c`** · Farsi: [`05-fault-tolerance-replication.fa.md`](05-fault-tolerance-replication.fa.md)

## Glossary

| Term | Meaning |
|---|---|
| **Failure model** | What a faulty node may do: crash (stop), omission (drop messages), timing (too slow), Byzantine (anything, including lying). |
| **Failure detector** | A component that *suspects* nodes, usually by missing heartbeats. Can be wrong in an asynchronous network. |
| **Primary-backup** | One primary executes and ships state/log to backups; a backup takes over on failure. |
| **State machine replication (SMR)** | Every replica runs the same deterministic commands in the same order (agreed by consensus). |
| **Quorum** | A subset of replicas whose agreement is enough; any two quorums intersect. |
| **Consensus** | Agreeing on one value (or one log entry) despite failures: Paxos, Raft. |
| **Term (Raft)** | A logical epoch number; at most one leader per term. |

## 1. Summary

- Fault tolerance = **redundancy + a rule for agreeing despite failures**. How many replicas you need depends on the failure model: `f+1` to survive f crashes if failures are detectable, `2f+1` for crash faults with majority quorums in an asynchronous network, `3f+1` for Byzantine faults.
- Two replication styles: **primary-backup** (simple, needs reliable failure detection) and **state machine replication** (replicas agree on a command log by consensus; Raft and Paxos are the standard protocols).
- Quorums make it work: with N replicas, reads of R and writes of W overlap whenever `R + W > N`; majorities (`⌊N/2⌋+1`) always overlap, which is why a partitioned minority cannot make progress, and why FLP (1985) says no deterministic protocol can guarantee both safety and termination in a fully asynchronous system with even one crash.

## 2. Detailed explanation

**Fault, error, failure.** A *fault* (bit flip, dead disk, cut cable) causes an *error* (wrong state) which may become a *failure* (wrong service). Fault tolerance stops errors from becoming failures, mostly by redundancy: in time (retry, note 01), in information (checksums, ECC, RAID parity) and in space (replicas, this note).

**Failure models, weakest to strongest assumption about the faulty node:**

| Model | Faulty node may | Replicas to tolerate f | Example |
|---|---|---|---|
| Fail-stop | crash, and others reliably learn it | f + 1 | hardware with a watchdog that powers off |
| Crash (asynchronous) | crash; others cannot tell crash from slowness | 2f + 1 (majority) | Raft, Paxos, ZooKeeper, etcd |
| Omission / timing | drop or delay messages | 2f + 1 + timeouts | lossy networks |
| Byzantine | anything: lie, equivocate | 3f + 1 | PBFT, blockchain BFT |

Why 2f+1 for crashes: a decision needs acknowledgements from a quorum Q; to stay live with f nodes down, `Q ≤ N − f`; to be safe, any two quorums must overlap (`2Q > N`). Both hold when `N = 2f+1`, `Q = f+1`. Why 3f+1 for Byzantine: the overlap of two quorums must contain at least one *honest* node even if f of the overlap lie: `2Q − N ≥ f + 1` with `Q = N − f` gives `N ≥ 3f + 1`.

**Failure detection** is a heartbeat plus a timeout. In an asynchronous network a slow node and a dead node look identical (the same "no reply" as RPC in note 01). A detector that suspects too early causes two primaries (**split brain**); one that suspects too late causes long outages. The Linux kernel uses the same pattern inside one machine: each CPU must periodically "touch" a timestamp, and the soft-lockup detector fires if it has not (§4).

**Primary-backup.** Clients talk to the primary; it applies the operation, sends the update to backups, waits for their acks, then replies. If the primary dies, a backup takes over. Simple and cheap (f+1 copies), but it trusts the failure detector: if the old primary is only slow, there are now two. Fix: **leases/epochs** (the primary may act only during a lease granted by a majority, and stale epochs are rejected; also called fencing).

**State machine replication.** Make every replica a deterministic state machine and feed them the same commands in the same order. The "same order" is a consensus problem, solved once per log slot.

**Raft preview** (Ongaro & Ousterhout 2014):

1. **Leader election.** Followers that miss heartbeats for a randomized election timeout become candidates, increment the **term**, vote for themselves and request votes. A majority vote makes a leader; one vote per node per term guarantees at most one leader per term.
2. **Log replication.** The leader appends a command, sends `AppendEntries(term, prevIndex, prevTerm, entries)`; a follower accepts only if its log has an entry at `prevIndex` with `prevTerm` (**log matching**). An entry is **committed** once stored on a majority; then it is applied.
3. **Safety.** A candidate's vote is refused if its log is less up to date than the voter's, so every new leader already contains all committed entries.

**FLP** (Fischer, Lynch & Paterson 1985): in an asynchronous system with even one possible crash, no deterministic consensus protocol can guarantee termination. Real systems keep **safety always** and get **liveness when the network behaves** (timeouts, randomized elections), which is exactly Raft's design.

**Quorum replication without a leader** (Dynamo, Cassandra): write to W replicas, read from R; `R + W > N` makes every read overlap the latest write. Concurrent writes still need versioning (vector clocks, note 02) to detect conflicts.

## 3. Diagram

```mermaid
sequenceDiagram
  participant C as Client
  participant L as Leader (term 3)
  participant F1 as Follower 1
  participant F2 as Follower 2
  C->>L: put(x, 5)
  L->>L: append log[7] = (term 3, x=5)
  par replicate
    L->>F1: AppendEntries(term 3, prev=6/3, [x=5])
    L->>F2: AppendEntries(term 3, prev=6/3, [x=5])
  end
  F1-->>L: ok (match log[7])
  Note over L: 2 of 3 have log[7] → committed
  L->>L: apply x=5
  L-->>C: ok
  F2--xL: (slow or partitioned; catches up later)
```

## 4. Worked example: quorum overlap by brute force, and the kernel's own failure detector

**(a) Which (R, W) are safe for N = 5?** A short Go program enumerates every read set of size R and every write set of size W and counts disjoint pairs (a disjoint pair = a read that can miss the latest write):

```go
for rs := uint(0); rs <= full; rs++ {
	if bits.OnesCount(rs) != r {
		continue
	}
	for ws := uint(0); ws <= full; ws++ {
		if bits.OnesCount(ws) == w && rs&ws == 0 {
			disjoint++
		}
	}
}
```

Real run, `golang:1.22` container on the host (`go1.22.12`), 2026-11-15:

```text
N=5 R=1 W=5  R+W>N=true   disjoint (R,W) pairs=0
N=5 R=2 W=4  R+W>N=true   disjoint (R,W) pairs=0
N=5 R=3 W=3  R+W>N=true   disjoint (R,W) pairs=0
N=5 R=2 W=3  R+W>N=false  disjoint (R,W) pairs=10
N=5 R=1 W=1  R+W>N=false  disjoint (R,W) pairs=20
```

- The first three rows satisfy `R + W > N`: zero disjoint pairs, every read sees the last write.
- `R=2, W=3`: each of the C(5,2) = 10 read pairs has exactly one disjoint write set (the other 3 nodes): 10 stale-read cases.
- `R=1, W=1`: 5 × 4 = 20. Fast, and wrong under concurrency.
- Trade-off: `R=1, W=5` gives fast reads but a write blocks if any one node is down; `R=W=3` (majority) tolerates 2 failures for both.

**(b) A heartbeat failure detector inside Linux.** Each CPU's watchdog thread updates a timestamp; a timer checks it:

`linux/kernel/watchdog.c · is_softlockup() · v6.18.63` ([Elixir L690](https://elixir.bootlin.com/linux/v6.18.63/source/kernel/watchdog.c#L690))

```c
  690  static int is_softlockup(unsigned long touch_ts,
  691  			 unsigned long period_ts,
  692  			 unsigned long now)
  693  {
  694  	if ((watchdog_enabled & WATCHDOG_SOFTOCKUP_ENABLED) && watchdog_thresh) {
  ...
  712  		if (time_after_eq(now, period_ts + get_softlockup_thresh() * 3 / 4))
  713  			scx_softlockup(now - touch_ts);
  714  
  715  		/* Warn about unreasonable delays. */
  716  		if (time_after(now, period_ts + get_softlockup_thresh()))
  717  			return now - touch_ts;
  718  	}
  719  	return 0;
  720  }
```

- `period_ts` is the heartbeat: the last time this CPU managed to run its watchdog task.
- **L716–717**: no heartbeat for longer than the threshold → report "soft lockup" with the stall length. The threshold is `watchdog_thresh * 2` (`get_softlockup_thresh()`, L601–603), and `watchdog_thresh` defaults to 10 (L49): 20 seconds.
- **L712–713**: at 3/4 of the threshold, it first tries a cheaper recovery: ask sched_ext to eject a misbehaving BPF scheduler. A graded response, like "suspect, then act".
- Same trade-off as distributed detectors: a CPU that is merely starved (e.g. a long non-preemptible section) is reported exactly like one that is truly stuck. A shorter threshold detects real hangs sooner and produces more false alarms.

## 5. Edge cases & pitfalls

- **Split brain**: two nodes both believe they are primary after a partition. Prevent with majority leases, epochs/terms and fencing tokens checked by the storage.
- **Even cluster sizes** buy nothing: 4 nodes tolerate 1 crash, same as 3, and a 2/2 partition stops both halves.
- **Correlated failures** (same rack, same kernel bug, same bad config push) break the independence assumption behind f.
- **Non-determinism in SMR** (timestamps, random numbers, thread scheduling, iteration order of hash maps) makes replicas diverge even with the same log. The leader must decide such values and log them.
- **Committed ≠ applied ≠ acknowledged to the client**: a crash between steps must not lose or double-apply a command; clients still need request IDs (note 01).
- **Reading from a follower** can return stale data; linearizable reads go through the leader with a quorum check or a lease.
- **Timeouts that are too tight** cause election storms on a loaded network: the cluster spends its time electing leaders instead of serving.

## 6. Exam-style key points

- Fail-stop: f+1; crash in asynchronous network: 2f+1 (majority quorums); Byzantine: 3f+1.
- Quorum safety: `R + W > N` (and `2W > N` to order concurrent writes); majority = `⌊N/2⌋ + 1`.
- Primary-backup relies on failure detection; SMR relies on consensus over a log.
- Raft: randomized election timeout, terms, one vote per term, `AppendEntries` with `(prevIndex, prevTerm)` log matching, commit on majority, up-to-date check on votes.
- FLP: no deterministic consensus guarantees termination in an asynchronous system with one crash; keep safety, get liveness via timeouts.
- Failure detectors suspect, they do not know. Kernel analogue: soft-lockup detector (`is_softlockup()`, threshold `2 × watchdog_thresh` = 20 s by default).
- Papers: Fischer, Lynch & Paterson (1985); Lamport, *Paxos Made Simple* (2001); Ongaro & Ousterhout (2014), *In Search of an Understandable Consensus Algorithm*.

## 7. Links

- Lesson: [`../lesson.en.md`](../lesson.en.md) §4.5 (fault tolerance)
- Labs: [`../labs/02-rpc-idempotency/`](../labs/02-rpc-idempotency/) (retries + idempotency are the client side of fault tolerance); [`../labs/01-lamport-vector-clocks/`](../labs/01-lamport-vector-clocks/) (the ordering problem consensus solves)
- Quiz: [`../quiz.en.md`](../quiz.en.md) Q13 (design a replicated KV store), oral O2 (vector-clock cost and alternatives)
- Related: [`01-rpc-semantics.en.md`](01-rpc-semantics.en.md) · [`02-lamport-vector-clocks.en.md`](02-lamport-vector-clocks.en.md)
