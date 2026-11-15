// rpcbank.go: a deposit RPC over Go's net/rpc with a lossy server, client-side
// timeouts and retries, and an optional server-side duplicate filter.
//
//	go build -o rpcbank rpcbank.go
//	./rpcbank server -addr 127.0.0.1:9650 -lose 0.3 -dedup=false &
//	./rpcbank client -addr 127.0.0.1:9650 -n 20 -timeout 200ms -retries 5
//
// "-lose p" makes the server execute the request and then delay the reply past
// the client's timeout with probability p: the request ran, but the reply is lost.
package main

import (
	"errors"
	"flag"
	"fmt"
	"log"
	"math/rand"
	"net"
	"net/rpc"
	"os"
	"sync"
	"time"
)

type DepositArgs struct {
	RequestID string // unique per logical operation, reused on every retry
	Amount    int64
}

type DepositReply struct {
	Balance int64
}

type Bank struct {
	mu       sync.Mutex
	balance  int64
	executed int64                   // how many times Deposit really ran
	dedup    bool                    // remember replies by RequestID
	replies  map[string]DepositReply // reply cache (grows forever: see extension)
	lose     float64
	rng      *rand.Rand
}

func (b *Bank) Deposit(args DepositArgs, reply *DepositReply) error {
	b.mu.Lock()
	if old, seen := b.replies[args.RequestID]; b.dedup && seen {
		*reply = old // duplicate: answer again, do not execute again
		b.mu.Unlock()
		return nil
	}
	b.balance += args.Amount
	b.executed++
	*reply = DepositReply{Balance: b.balance}
	if b.dedup {
		b.replies[args.RequestID] = *reply
	}
	slow := b.rng.Float64() < b.lose
	b.mu.Unlock()
	if slow {
		time.Sleep(500 * time.Millisecond) // the reply arrives after the client gave up
	}
	return nil
}

// Stats lets the client read the server's view at the end.
func (b *Bank) Stats(_ int, out *[2]int64) error {
	b.mu.Lock()
	defer b.mu.Unlock()
	*out = [2]int64{b.balance, b.executed}
	return nil
}

func serve(addr string, lose float64, dedup bool, seed int64) error {
	bank := &Bank{dedup: dedup, replies: map[string]DepositReply{}, lose: lose, rng: rand.New(rand.NewSource(seed))}
	if err := rpc.Register(bank); err != nil {
		return err
	}
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return err
	}
	log.Printf("server on %s lose=%.2f dedup=%v", addr, lose, dedup)
	rpc.Accept(ln)
	return nil
}

var errTimeout = errors.New("timeout")

// callWithTimeout issues one RPC and gives up after d. The request may still run.
func callWithTimeout(c *rpc.Client, method string, args any, reply any, d time.Duration) error {
	call := c.Go(method, args, reply, make(chan *rpc.Call, 1))
	select {
	case <-call.Done:
		return call.Error
	case <-time.After(d):
		return errTimeout
	}
}

func client(addr string, n int, timeout time.Duration, retries int) error {
	c, err := rpc.Dial("tcp", addr)
	if err != nil {
		return err
	}
	defer c.Close()
	sent, retried, failed := 0, 0, 0
	for i := 0; i < n; i++ {
		args := DepositArgs{RequestID: fmt.Sprintf("dep-%d-%d", os.Getpid(), i), Amount: 10}
		ok := false
		for attempt := 0; attempt <= retries; attempt++ {
			sent++
			if attempt > 0 {
				retried++
			}
			reply := new(DepositReply) // fresh per attempt: a late reply must not overwrite it
			if err := callWithTimeout(c, "Bank.Deposit", args, reply, timeout); err == nil {
				ok = true
				break
			}
		}
		if !ok {
			failed++
		}
	}
	var st [2]int64
	if err := c.Call("Bank.Stats", 0, &st); err != nil {
		return err
	}
	fmt.Printf("logical deposits=%d  rpcs sent=%d  retries=%d  gave up=%d\n", n, sent, retried, failed)
	fmt.Printf("expected balance=%d  server balance=%d  executions=%d\n", int64(n)*10, st[0], st[1])
	return nil
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: rpcbank server|client [flags]")
		os.Exit(2)
	}
	fs := flag.NewFlagSet(os.Args[1], flag.ExitOnError)
	addr := fs.String("addr", "127.0.0.1:9650", "listen/dial address")
	lose := fs.Float64("lose", 0.3, "server: probability that a reply is late")
	dedup := fs.Bool("dedup", false, "server: filter duplicate RequestIDs")
	seed := fs.Int64("seed", 1, "server: random seed")
	n := fs.Int("n", 20, "client: logical deposits")
	timeout := fs.Duration("timeout", 200*time.Millisecond, "client: per-attempt timeout")
	retries := fs.Int("retries", 5, "client: retries per deposit")
	_ = fs.Parse(os.Args[2:])
	var err error
	switch os.Args[1] {
	case "server":
		err = serve(*addr, *lose, *dedup, *seed)
	case "client":
		err = client(*addr, *n, *timeout, *retries)
	default:
		err = fmt.Errorf("unknown mode %q", os.Args[1])
	}
	if err != nil {
		log.Fatal(err)
	}
}
