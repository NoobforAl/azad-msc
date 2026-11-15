// clocks.go: three processes exchange UDP messages on localhost and stamp
// every event with a Lamport clock and a vector clock.
//
//	go build -o clocks clocks.go
//	./clocks -id 0 -n 3 -events 6 -seed 1 > p0.log &   (same for -id 1, -id 2)
//	./clocks -analyze p0.log p1.log p2.log
package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"math/rand"
	"net"
	"os"
	"sort"
	"sync"
	"time"
)

const basePort int = 9600

// Event is one line of a process log (JSON).
type Event struct {
	Proc    int    `json:"proc"`
	Kind    string `json:"kind"` // LOCAL, SEND, RECV
	MsgID   string `json:"msg,omitempty"`
	Peer    int    `json:"peer"`
	Lamport uint64 `json:"L"`
	Vector  []int  `json:"V"`
}

// Msg is the wire format: the sender's clocks travel with the payload.
type Msg struct {
	From    int    `json:"from"`
	ID      string `json:"id"`
	Lamport uint64 `json:"L"`
	Vector  []int  `json:"V"`
}

type node struct {
	mu      sync.Mutex
	id      int
	lamport uint64
	vector  []int
	out     *json.Encoder
}

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

func (n *node) log(kind string, id string, peer int) {
	v := append([]int(nil), n.vector...)
	_ = n.out.Encode(Event{Proc: n.id, Kind: kind, MsgID: id, Peer: peer, Lamport: n.lamport, Vector: v})
}

func run(id, procs, events int, seed int64) error {
	conn, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1), Port: basePort + id})
	if err != nil {
		return err
	}
	defer conn.Close()
	n := &node{id: id, vector: make([]int, procs), out: json.NewEncoder(os.Stdout)}
	rng := rand.New(rand.NewSource(seed + int64(id)))

	go func() { // receiver
		buf := make([]byte, 2048)
		for {
			k, _, err := conn.ReadFromUDP(buf)
			if err != nil {
				return
			}
			var m Msg
			if json.Unmarshal(buf[:k], &m) != nil {
				continue
			}
			n.mu.Lock()
			n.merge(m)
			n.log("RECV", m.ID, m.From)
			n.mu.Unlock()
		}
	}()

	time.Sleep(300 * time.Millisecond) // let the other processes bind their ports
	for e := 0; e < events; e++ {
		time.Sleep(time.Duration(50+rng.Intn(150)) * time.Millisecond)
		n.mu.Lock()
		n.tick()
		if rng.Intn(3) == 0 {
			n.log("LOCAL", "", -1)
			n.mu.Unlock()
			continue
		}
		peer := (id + 1 + rng.Intn(procs-1)) % procs
		m := Msg{From: id, ID: fmt.Sprintf("%d-%d", id, e), Lamport: n.lamport, Vector: append([]int(nil), n.vector...)}
		n.log("SEND", m.ID, peer)
		n.mu.Unlock()
		b, _ := json.Marshal(m)
		if _, err := conn.WriteToUDP(b, &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1), Port: basePort + peer}); err != nil {
			return err
		}
	}
	time.Sleep(time.Second) // drain late messages before exiting
	return nil
}

// leq reports a <= b component-wise; a -> b (happened-before) iff leq(a,b) && a != b.
func leq(a, b []int) bool {
	for k := range a {
		if a[k] > b[k] {
			return false
		}
	}
	return true
}

func before(a, b []int) bool { return leq(a, b) && !leq(b, a) }

func analyze(files []string) error {
	var all []Event
	for _, f := range files {
		fh, err := os.Open(f)
		if err != nil {
			return err
		}
		sc := bufio.NewScanner(fh)
		for sc.Scan() {
			var ev Event
			if json.Unmarshal(sc.Bytes(), &ev) == nil {
				all = append(all, ev)
			}
		}
		fh.Close()
	}
	// Clock condition: for every message, send -> recv in both clocks.
	sends := map[string]Event{}
	for _, ev := range all {
		if ev.Kind == "SEND" {
			sends[ev.MsgID] = ev
		}
	}
	msgs, okL, okV := 0, 0, 0
	for _, ev := range all {
		if s, found := sends[ev.MsgID]; found && ev.Kind == "RECV" {
			msgs++
			if s.Lamport < ev.Lamport {
				okL++
			}
			if before(s.Vector, ev.Vector) {
				okV++
			}
		}
	}
	fmt.Printf("events=%d messages=%d  clock condition: lamport %d/%d, vector %d/%d\n", len(all), msgs, okL, msgs, okV, msgs)

	// Lamport total order: sort by (L, proc). Ties are broken by process id.
	sort.Slice(all, func(i, j int) bool {
		if all[i].Lamport != all[j].Lamport {
			return all[i].Lamport < all[j].Lamport
		}
		return all[i].Proc < all[j].Proc
	})
	fmt.Println("total order (L, proc):")
	for _, ev := range all {
		fmt.Printf("  L=%-3d P%d %-5s %-4s V=%v\n", ev.Lamport, ev.Proc, ev.Kind, ev.MsgID, ev.Vector)
	}
	// Pairs that Lamport orders but that are really concurrent.
	pairs, shown := 0, 0
	for i := range all {
		for j := range all {
			a, b := all[i], all[j]
			if a.Proc != b.Proc && a.Lamport < b.Lamport && !before(a.Vector, b.Vector) && !before(b.Vector, a.Vector) {
				pairs++
				if shown < 3 {
					fmt.Printf("concurrent but L(a)<L(b): P%d %s L=%d V=%v  ||  P%d %s L=%d V=%v\n",
						a.Proc, a.Kind, a.Lamport, a.Vector, b.Proc, b.Kind, b.Lamport, b.Vector)
					shown++
				}
			}
		}
	}
	fmt.Printf("pairs with L(a)<L(b) that are concurrent (a || b): %d\n", pairs)
	return nil
}

func main() {
	id := flag.Int("id", 0, "process id (0..n-1)")
	procs := flag.Int("n", 3, "number of processes")
	events := flag.Int("events", 6, "events per process")
	seed := flag.Int64("seed", 1, "random seed")
	doAnalyze := flag.Bool("analyze", false, "analyze log files given as arguments")
	flag.Parse()
	var err error
	if *doAnalyze {
		err = analyze(flag.Args())
	} else {
		err = run(*id, *procs, *events, *seed)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
}
