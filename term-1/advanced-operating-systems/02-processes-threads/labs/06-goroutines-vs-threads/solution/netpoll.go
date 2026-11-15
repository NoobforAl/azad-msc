// netpoll.go: solution to the lab 02.6 extension.
// Same 200 goroutines waiting on a pipe, but the read end is non-blocking and
// wrapped in an *os.File, so reads go through the Go netpoller (epoll): a
// goroutine that would block is parked in the runtime and no OS thread is held.
//
// Build: go build -o netpoll netpoll.go
// Run:   ./netpoll 200 ; then compare with ../gvt syscall 200
package main

import (
	"fmt"
	"os"
	"runtime"
	"strconv"
	"syscall"
	"time"
)

func threads() int {
	e, err := os.ReadDir("/proc/self/task")
	if err != nil {
		panic(err)
	}
	return len(e)
}

func main() {
	n := 200
	if len(os.Args) > 1 {
		v, err := strconv.Atoi(os.Args[1])
		if err != nil {
			panic(err)
		}
		n = v
	}
	var fds [2]int
	if err := syscall.Pipe2(fds[:], syscall.O_NONBLOCK|syscall.O_CLOEXEC); err != nil {
		panic(err)
	}
	// os.NewFile on a non-blocking fd registers it with the netpoller.
	r := os.NewFile(uintptr(fds[0]), "pipe-r")
	fmt.Printf("start:    goroutines=%-5d os_threads=%d\n", runtime.NumGoroutine(), threads())
	for i := 0; i < n; i++ {
		go func() {
			b := make([]byte, 1)
			r.Read(b) // parks the goroutine in the runtime, not the thread in the kernel
		}()
	}
	time.Sleep(time.Second)
	fmt.Printf("after 1s: goroutines=%-5d os_threads=%d\n", runtime.NumGoroutine(), threads())
	ents, _ := os.ReadDir("/proc/self/fd")
	for _, e := range ents {
		if l, err := os.Readlink("/proc/self/fd/" + e.Name()); err == nil && l == "anon_inode:[eventpoll]" {
			fmt.Printf("fd %s -> %s (the netpoller's epoll instance)\n", e.Name(), l)
		}
	}
}
