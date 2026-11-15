// pc_chan.go: the same bounded buffer as a buffered Go channel.
// The channel's capacity is the buffer size; the runtime does the
// counting, locking and parking that pc_sem.c and pc_cond.c do by hand.
// Run: go run pc_chan.go <items> <buffer-size>
package main

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

func main() {
	items, capacity := int64(1000000), 16
	if len(os.Args) > 1 {
		items, _ = strconv.ParseInt(os.Args[1], 10, 64)
	}
	if len(os.Args) > 2 {
		capacity, _ = strconv.Atoi(os.Args[2])
	}

	ch := make(chan int64, capacity)
	done := make(chan int64)

	start := time.Now()
	go func() { // producer
		for i := int64(1); i <= items; i++ {
			ch <- i // blocks while the buffer is full
		}
		close(ch) // no more items: lets the consumer's range loop end
	}()
	go func() { // consumer
		var sum int64
		for v := range ch { // blocks while the buffer is empty
			sum += v
		}
		done <- sum
	}()
	sum := <-done
	dt := time.Since(start)

	want := items * (items + 1) / 2
	status := "WRONG"
	if sum == want {
		status = "OK"
	}
	fmt.Printf("chan  items=%d cap=%d sum=%d %s time=%.3fs ns/item=%.0f\n",
		items, capacity, sum, status, dt.Seconds(), float64(dt.Nanoseconds())/float64(items))
}
