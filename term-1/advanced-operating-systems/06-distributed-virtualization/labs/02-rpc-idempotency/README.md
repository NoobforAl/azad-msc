# Lab 06.2 — RPC with timeouts, retries and an idempotency filter

**Goal:** see at-most-once, at-least-once and exactly-once *effect* happen to the same 20 deposits, and build the server-side duplicate filter that makes retries safe.

Runs anywhere with Go ≥ 1.21 (user space). Ports: TCP 9650–9652 on 127.0.0.1.

## Steps

```bash
cd ~/work/06-distributed-virtualization/02-rpc-idempotency
bash run.sh

# by hand: a server that loses 50% of replies, no dedup, then a client with 3 retries
go build -o rpcbank rpcbank.go
./rpcbank server -addr 127.0.0.1:9660 -lose 0.5 -dedup=false &
./rpcbank client -addr 127.0.0.1:9660 -n 10 -timeout 200ms -retries 3
kill %1
```

## Code

[`rpcbank.go`](rpcbank.go) uses Go's standard `net/rpc` over TCP.

| Piece | What it does |
|---|---|
| `DepositArgs{RequestID, Amount}` | `RequestID` is unique per **logical** deposit and **reused on every retry** |
| `Bank.Deposit` | executes `balance += Amount`; with `-lose p` it then sleeps 500 ms with probability p, so the reply arrives after the client's 200 ms timeout. The request **did run**. |
| `-dedup=true` | keeps `replies[RequestID]`; a repeated ID gets the stored reply and is **not executed again** |
| `callWithTimeout` | `client.Go(...)` + `select` on `call.Done` / `time.After(d)`: the client stops waiting, but cannot cancel the server |
| `Bank.Stats` | the server's own count of executions, read at the end |

```go
func (b *Bank) Deposit(args DepositArgs, reply *DepositReply) error {
	b.mu.Lock()
	if old, seen := b.replies[args.RequestID]; b.dedup && seen {
		*reply = old // duplicate: answer again, do not execute again
		b.mu.Unlock()
		return nil
	}
	b.balance += args.Amount
	b.executed++
	/* ... store reply if dedup, maybe sleep past the client's timeout ... */
```

The kernel has the same filter: the Linux NFS server's duplicate reply cache, `fs/nfsd/nfscache.c` · `nfsd_cache_lookup()` (see [note 01](../../notes/01-rpc-semantics.en.md)).

## Expected output

> Real output, captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. Shared 8-vCPU guest: timings and interleavings differ on every run; the invariants do not.

```
$ bash run.sh
== A: retries=0 dedup=false (at-most-once)
logical deposits=20  rpcs sent=20  retries=0  gave up=8
expected balance=200  server balance=200  executions=20
== B: retries=5 dedup=false (at-least-once)
logical deposits=20  rpcs sent=29  retries=9  gave up=0
expected balance=200  server balance=290  executions=29
== C: retries=5 dedup=true  (exactly-once effect)
logical deposits=20  rpcs sent=28  retries=8  gave up=0
expected balance=200  server balance=200  executions=20
```

Extension solution (`go run rpcbank_seq.go`, same VM):

```
expected=600 balance=600 executions=60 cache entries=3
```

## What to observe

- **A: "gave up" is not "did not run".** The client gave up on some deposits, but `executions=20`: every one ran; only the replies were late. The client is left *not knowing* the outcome. That is at-most-once.
- **B: retries without a filter = duplicates.** Every retry that reached the server executed again: `executions = 20 + retries`, and the balance is wrong by `10 × retries`.
- **C: same retry pattern, correct balance.** `executions=20`. Retries hit the reply cache. At-least-once delivery + dedup = exactly-once effect.
- **TCP did not help.** All three runs use one TCP connection with no packet loss. Duplicates came from the *application* retrying after its own timeout.
- `sent` differs between B and C because the server's random "slow" choice is drawn only for executed requests: duplicates answered from the cache draw nothing.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `bind: address already in use` | a server from a previous run is alive | `pkill -f 'rpcbank server'` |
| balance correct in B | `-lose 0` or timeout longer than 500 ms | keep `-timeout 200ms`, `-lose 0.3` |
| dedup "works" but memory grows | `replies` map keeps every ID forever | extension below |
| duplicates with dedup on | client generated a **new** ID per attempt | create the ID once per logical operation, outside the retry loop |

## Extension

The reply cache grows by one entry per request forever. Bound it: give each client an ID and strictly increasing sequence numbers (one outstanding request per client), keep **one** `(seq, reply)` entry per client, treat `seq == last` as a retry and `seq < last` as stale. Run 3 concurrent clients × 20 deposits with 30% late replies and show: correct balance, 60 executions, 3 cache entries.

Solution: [`solution/rpcbank_seq.go`](solution/rpcbank_seq.go) (`go run rpcbank_seq.go`).

Related: [note 01](../../notes/01-rpc-semantics.en.md) · [lesson §4.1](../../lesson.en.md) · quiz Q1, Q9.
