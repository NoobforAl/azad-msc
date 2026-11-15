// causal.go: solution to the Lab 06.1 extension. Causal broadcast with a
// hold-back queue (Birman-Schiper-Stephenson rule), 3 processes on localhost UDP.
//
//	go build -o causal causal.go
//	for i in 0 1 2; do ./causal -id $i & done; wait
//
// Every broadcast is delayed 0-300 ms per destination, so messages can arrive
// before the messages they causally depend on. The receiver holds such a message
// until it becomes deliverable:
//
//	deliver m from j  iff  Vm[j] == V[j]+1  and  Vm[k] <= V[k] for all k != j
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"math/rand"
	"net"
	"sync"
	"time"
)

const basePort int = 9700

type Msg struct {
	From   int    `json:"from"`
	Text   string `json:"text"`
	Vector []int  `json:"V"`
}

type node struct {
	mu      sync.Mutex
	id      int
	vector  []int // V[k] = number of messages from k delivered here
	pending []Msg // hold-back queue
	held    int
}

func (n *node) deliverable(m Msg) bool {
	for k := range n.vector {
		if k == m.From {
			if m.Vector[k] != n.vector[k]+1 {
				return false
			}
		} else if m.Vector[k] > n.vector[k] {
			return false
		}
	}
	return true
}

// receive queues m, then delivers everything that has become deliverable.
func (n *node) receive(m Msg) {
	n.mu.Lock()
	defer n.mu.Unlock()
	n.pending = append(n.pending, m)
	if !n.deliverable(m) {
		n.held++
		fmt.Printf("P%d HOLD    %-6s V=%v local=%v\n", n.id, m.Text, m.Vector, n.vector)
	}
	for progress := true; progress; {
		progress = false
		for i, p := range n.pending {
			if n.deliverable(p) {
				n.vector[p.From]++
				fmt.Printf("P%d DELIVER %-6s V=%v local=%v\n", n.id, p.Text, p.Vector, n.vector)
				n.pending = append(n.pending[:i], n.pending[i+1:]...)
				progress = true
				break
			}
		}
	}
}

func main() {
	id := flag.Int("id", 0, "process id")
	procs := flag.Int("n", 3, "processes")
	count := flag.Int("msgs", 4, "broadcasts per process")
	flag.Parse()
	conn, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1), Port: basePort + *id})
	if err != nil {
		panic(err)
	}
	n := &node{id: *id, vector: make([]int, *procs)}
	go func() {
		buf := make([]byte, 2048)
		for {
			k, _, err := conn.ReadFromUDP(buf)
			if err != nil {
				return
			}
			var m Msg
			if json.Unmarshal(buf[:k], &m) == nil {
				n.receive(m)
			}
		}
	}()
	rng := rand.New(rand.NewSource(int64(*id) + 42))
	time.Sleep(300 * time.Millisecond)
	for e := 0; e < *count; e++ {
		time.Sleep(time.Duration(rng.Intn(120)) * time.Millisecond)
		n.mu.Lock()
		n.vector[n.id]++ // a broadcast counts as delivered locally
		m := Msg{From: n.id, Text: fmt.Sprintf("m%d.%d", n.id, e), Vector: append([]int(nil), n.vector...)}
		n.mu.Unlock()
		b, _ := json.Marshal(m)
		for p := 0; p < *procs; p++ {
			if p == n.id {
				continue
			}
			delay := time.Duration(rng.Intn(300)) * time.Millisecond
			go func(port int, d time.Duration) {
				time.Sleep(d)
				_, _ = conn.WriteToUDP(b, &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1), Port: port})
			}(basePort+p, delay)
		}
	}
	time.Sleep(1500 * time.Millisecond)
	n.mu.Lock()
	fmt.Printf("P%d done: final V=%v held=%d still-pending=%d\n", n.id, n.vector, n.held, len(n.pending))
	n.mu.Unlock()
}
