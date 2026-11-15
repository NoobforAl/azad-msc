// gvt.go: goroutines are not OS threads. Count both.
//
// Modes (N goroutines each):
//   sleep    N goroutines blocked in time.Sleep  -> parked in the Go runtime, no thread each
//   cpu      N goroutines spinning               -> at most GOMAXPROCS run at once
//   syscall  N goroutines blocked in read(2) on a pipe, made with syscall.Read so the
//            runtime's netpoller cannot help -> each blocked goroutine pins an OS thread (M)
//
// The kernel only knows threads: we count them in /proc/self/task, the same
// list `ps -L` and `top -H` use. Each entry there is one task_struct.
//
// Build: go build -o gvt gvt.go
// Run:   ./gvt sleep 10000 ; GOMAXPROCS=2 ./gvt cpu 100 ; ./gvt syscall 200
package main

import (
	"fmt"
	"os"
	"runtime"
	"strconv"
	"strings"
	"syscall"
	"time"
)

// osThreads counts entries in /proc/self/task: one per kernel task (thread).
func osThreads() int {
	ents, err := os.ReadDir("/proc/self/task")
	if err != nil {
		panic(err)
	}
	return len(ents)
}

// vmRSS returns the VmRSS line of /proc/self/status.
func vmRSS() string {
	b, err := os.ReadFile("/proc/self/status")
	if err != nil {
		panic(err)
	}
	for _, l := range strings.Split(string(b), "\n") {
		if strings.HasPrefix(l, "VmRSS:") {
			return strings.Join(strings.Fields(l)[1:], " ")
		}
	}
	return "?"
}

func main() {
	if len(os.Args) != 3 {
		fmt.Fprintln(os.Stderr, "usage: gvt sleep|cpu|syscall N")
		os.Exit(2)
	}
	mode := os.Args[1]
	n, err := strconv.Atoi(os.Args[2])
	if err != nil {
		panic(err)
	}
	fmt.Printf("pid=%d GOMAXPROCS=%d NumCPU=%d\n", os.Getpid(), runtime.GOMAXPROCS(0), runtime.NumCPU())
	fmt.Printf("start:   goroutines=%-6d os_threads=%-4d VmRSS=%s\n", runtime.NumGoroutine(), osThreads(), vmRSS())

	t0 := time.Now()
	switch mode {
	case "sleep":
		for i := 0; i < n; i++ {
			go func() { time.Sleep(time.Hour) }()
		}
	case "cpu":
		for i := 0; i < n; i++ {
			go func() {
				for {
				}
			}()
		}
	case "syscall":
		var fds [2]int
		if err := syscall.Pipe(fds[:]); err != nil {
			panic(err)
		}
		for i := 0; i < n; i++ {
			go func() {
				buf := make([]byte, 1)
				syscall.Read(fds[0], buf) // blocks in the kernel: this M is stuck with it
			}()
		}
	default:
		fmt.Fprintln(os.Stderr, "unknown mode")
		os.Exit(2)
	}

	spawn := time.Since(t0)
	fmt.Printf("spawned %d goroutines in %v (%.2f us each)\n", n, spawn, float64(spawn.Microseconds())/float64(n))
	time.Sleep(1 * time.Second)
	fmt.Printf("after 1s: goroutines=%-6d os_threads=%-4d VmRSS=%s\n", runtime.NumGoroutine(), osThreads(), vmRSS())
}
