# Lab 06.1 — Lamport and vector clocks across three processes

**Goal:** stamp every event of three real processes (UDP on localhost) with a Lamport clock and a vector clock, then prove from the logs that both respect happened-before and that only the vectors detect concurrency.

Runs anywhere with Go ≥ 1.21 (user space, no root). Ports used: UDP 9600–9602.

## Steps

```bash
cd ~/work/06-distributed-virtualization/01-lamport-vector-clocks
go version
bash run.sh                       # build, start P0 P1 P2 in parallel, analyze
head -3 p1.log                    # raw JSON events of one process
SEED=7 EVENTS=10 bash run.sh      # another history: same invariants, different numbers
```

`run.sh` does: `go build -o clocks clocks.go`, then `./clocks -id i -n 3 -events 6 -seed 1 > p$i.log &` for i = 0..2, `wait`, and `./clocks -analyze p0.log p1.log p2.log`.

## Code

[`clocks.go`](clocks.go) (~230 lines). The two clock rules are 15 lines:

```go
// tick is the rule for LOCAL and SEND events: L++, V[i]++.
func (n *node) tick() {
	n.lamport++
	n.vector[n.id]++
}

// merge is the rule for RECV: L = max(L, Lm) + 1, V = max(V, Vm) then V[i]++.
func (n *node) merge(m Msg) {
	if m.Lamport > n.lamport {
		n.lamport = m.Lamport
	}
	n.lamport++
	for k := range n.vector {
		if m.Vector[k] > n.vector[k] {
			n.vector[k] = m.Vector[k]
		}
	}
	n.vector[n.id]++
}
```

- Each process has one receiver goroutine and one sender loop; a mutex makes "update clock + log the event" atomic, so the log order inside one process is the real event order.
- The sender's clocks travel inside every message (`Msg.Lamport`, `Msg.Vector`).
- `-analyze` checks, for every message, that `L(send) < L(recv)` and `V(send) < V(recv)`, prints the Lamport total order `(L, proc)`, and counts pairs from different processes with `L(a) < L(b)` whose vectors are incomparable (a ∥ b).

## Expected output

> Real output, captured on aos-lab (VirtualBox, Ubuntu 24.04, Linux 6.18.63), 2026-11-15. Shared 8-vCPU guest: timings and interleavings differ on every run; the invariants do not.

```
$ bash run.sh
   8 p0.log
  10 p1.log
  10 p2.log
  28 total
events=28 messages=10  clock condition: lamport 10/10, vector 10/10
total order (L, proc):
  L=1   P1 LOCAL      V=[0 1 0]
  L=1   P2 SEND  2-0  V=[0 0 1]
  L=2   P0 RECV  2-0  V=[1 0 1]
  L=2   P2 SEND  2-1  V=[0 0 2]
  L=3   P0 LOCAL      V=[2 0 1]
  L=3   P1 RECV  2-1  V=[0 2 2]
  L=4   P0 SEND  0-1  V=[3 0 1]
  L=4   P1 SEND  1-1  V=[0 3 2]
  ...
  L=13  P2 RECV  1-5  V=[7 10 9]
  L=14  P2 SEND  2-5  V=[7 10 10]
  L=15  P0 RECV  2-5  V=[8 10 10]
concurrent but L(a)<L(b): P1 LOCAL L=1 V=[0 1 0]  ||  P0 RECV L=2 V=[1 0 1]
concurrent but L(a)<L(b): P1 LOCAL L=1 V=[0 1 0]  ||  P2 SEND L=2 V=[0 0 2]
concurrent but L(a)<L(b): P1 LOCAL L=1 V=[0 1 0]  ||  P0 LOCAL L=3 V=[2 0 1]
pairs with L(a)<L(b) that are concurrent (a || b): 85
$ head -3 p1.log
{"proc":1,"kind":"LOCAL","peer":-1,"L":1,"V":[0,1,0]}
{"proc":1,"kind":"RECV","msg":"2-1","peer":2,"L":3,"V":[0,2,2]}
{"proc":1,"kind":"SEND","msg":"1-1","peer":2,"L":4,"V":[0,3,2]}
```

Extension solution run (`solution/causal.go`, same VM), last lines:

```
P2 DELIVER m0.3   V=[4 1 0] local=[4 4 4]
P1 DELIVER m0.3   V=[4 1 0] local=[4 4 3]
P1 DELIVER m2.3   V=[3 4 4] local=[4 4 4]
P0 DELIVER m2.2   V=[2 0 3] local=[4 4 3]
P0 DELIVER m2.3   V=[3 4 4] local=[4 4 4]
P1 done: final V=[4 4 4] held=1 still-pending=0
P0 done: final V=[4 4 4] held=3 still-pending=0
P2 done: final V=[4 4 4] held=4 still-pending=0
```

## What to observe

- **Clock condition holds for every message** in both clocks (`lamport n/n, vector n/n`). That is a theorem, not luck: `merge()` makes the receive strictly larger than the send.
- **Lamport ties.** Several events share the same `L` on different processes. The total order breaks ties by process id, which is arbitrary but consistent: every process that sorts the same events gets the same order (the basis of Lamport's mutual-exclusion algorithm).
- **Concurrent pairs.** Many pairs have `L(a) < L(b)` but incomparable vectors. If you sort a distributed log by Lamport time, those pairs look ordered although no message connects them. Only the vectors show it.
- **Same process ⇒ always ordered.** The analyzer skips same-process pairs: within a process the vector's own entry grows on every event, so they are always comparable.
- **UDP on localhost did not lose anything here**, but nothing in the clocks depends on delivery. A lost message simply produces no RECV event; the condition still holds for the delivered ones.

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `bind: address already in use` | a previous run is still alive, or another user on the VM uses 9600–9602 | `pkill -f './clocks -id'`; or change `basePort` |
| `messages=0` | processes started before the others were listening, all sends lost | the 300 ms start delay in `run()` covers it; don't remove it |
| `vector k/n` with k < n | clock updated outside the mutex, or the vector slice shared between message and node | copy the slice (`append([]int(nil), v...)`), lock around update + log |
| Different numbers each run | goroutine scheduling and sleep jitter | expected; the invariants (n/n) must not change |

## Extension

Turn sends into **causal broadcast**: every message goes to both peers, each copy delayed 0–300 ms so that copies overtake each other. Implement the hold-back queue so a message from j is delivered only when `Vm[j] == V[j] + 1` and `Vm[k] ≤ V[k]` for all k ≠ j. Print every HOLD and DELIVER, and show that the final vectors are equal on all three processes and nothing stays pending.

Solution: [`solution/causal.go`](solution/causal.go) (Birman–Schiper–Stephenson rule).

Related: [note 02](../../notes/02-lamport-vector-clocks.en.md) · [lesson §4.2](../../lesson.en.md) · quiz Q2, Q3.
