// rpcbank_seq.go: solution to the Lab 06.2 extension.
// The reply cache in rpcbank.go grows by one entry per request forever.
// Here each client has an ID and sends strictly increasing sequence numbers,
// one outstanding request at a time. The server keeps ONE entry per client:
// (last seq, last reply). Memory is O(clients), not O(requests).
//
//	go build -o rpcbank_seq rpcbank_seq.go && ./rpcbank_seq
//
// It runs server and client in one process (net/rpc over a real TCP socket).
package main

import (
	"errors"
	"fmt"
	"math/rand"
	"net"
	"net/rpc"
	"sync"
	"time"
)

type Args struct {
	ClientID uint64
	Seq      uint64 // 1, 2, 3, ... reused unchanged on retries
	Amount   int64
}

type Reply struct{ Balance int64 }

type entry struct {
	seq   uint64
	reply Reply
}

type Bank struct {
	mu       sync.Mutex
	balance  int64
	executed int64
	last     map[uint64]entry // one entry per client
	rng      *rand.Rand
}

var errStale = errors.New("stale request: seq below the last executed one")

func (b *Bank) Deposit(a Args, r *Reply) error {
	b.mu.Lock()
	e := b.last[a.ClientID]
	switch {
	case a.Seq == e.seq: // retry of the last request: replay the reply
		*r = e.reply
		b.mu.Unlock()
		return nil
	case a.Seq < e.seq: // the client already got an answer for a newer request
		b.mu.Unlock()
		return errStale
	}
	b.balance += a.Amount
	b.executed++
	*r = Reply{Balance: b.balance}
	b.last[a.ClientID] = entry{seq: a.Seq, reply: *r} // overwrites: implicit ack of seq-1
	slow := b.rng.Float64() < 0.3
	b.mu.Unlock()
	if slow {
		time.Sleep(500 * time.Millisecond)
	}
	return nil
}

func (b *Bank) Stats(_ int, out *[3]int64) error {
	b.mu.Lock()
	defer b.mu.Unlock()
	*out = [3]int64{b.balance, b.executed, int64(len(b.last))}
	return nil
}

func main() {
	bank := &Bank{last: map[uint64]entry{}, rng: rand.New(rand.NewSource(7))}
	if err := rpc.Register(bank); err != nil {
		panic(err)
	}
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		panic(err)
	}
	go rpc.Accept(ln)

	const clients, deposits = 3, 20
	var wg sync.WaitGroup
	for id := uint64(1); id <= clients; id++ {
		wg.Add(1)
		go func(id uint64) {
			defer wg.Done()
			c, err := rpc.Dial("tcp", ln.Addr().String())
			if err != nil {
				panic(err)
			}
			defer c.Close()
			for seq := uint64(1); seq <= deposits; seq++ {
				for { // retry until success: same (ClientID, Seq) every time
					call := c.Go("Bank.Deposit", Args{ClientID: id, Seq: seq, Amount: 10}, new(Reply), make(chan *rpc.Call, 1))
					select {
					case <-call.Done:
					case <-time.After(200 * time.Millisecond):
						continue
					}
					if call.Error == nil {
						break
					}
				}
			}
		}(id)
	}
	wg.Wait()
	c, _ := rpc.Dial("tcp", ln.Addr().String())
	var st [3]int64
	_ = c.Call("Bank.Stats", 0, &st)
	fmt.Printf("expected=%d balance=%d executions=%d cache entries=%d\n", clients*deposits*10, st[0], st[1], st[2])
}
