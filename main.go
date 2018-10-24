package main

import (
	// "bytes"
	"fmt"
	"os"
	"runtime"
	"sort"
	"strings"
	"time"
)

func doWork() {
	for {
		<-time.After(1 * time.Second)
	}
	x := 1 + 1
	fmt.Println("x::", x)
}

func main() {
	for i := 0; i < 10; i++ {
		go doWork()
	}

	fmt.Println("work done")

	if goroutineLeaked() {
		fmt.Println("LEAAKED GOROUTINES")
	} else {
		fmt.Println("no leak")
	}

}

func interestingGoroutines() (gs []string) {
	buf := make([]byte, 2<<20)
	buf = buf[:runtime.Stack(buf, true)]
	for _, g := range strings.Split(string(buf), "\n\n") {
		sl := strings.SplitN(g, "\n", 2)
		if len(sl) != 2 {
			continue
		}
		stack := strings.TrimSpace(sl[1])
		if stack == "" ||
			strings.Contains(stack, "testing.(*M).before.func1") ||
			strings.Contains(stack, "os/signal.signal_recv") ||
			strings.Contains(stack, "created by net.startServer") ||
			strings.Contains(stack, "created by testing.RunTests") ||
			strings.Contains(stack, "closeWriteAndWait") ||
			strings.Contains(stack, "testing.Main(") ||
			// These only show up with GOTRACEBACK=2; Issue 5005 (comment 28)
			strings.Contains(stack, "runtime.goexit") ||
			strings.Contains(stack, "created by runtime.gc") ||
			strings.Contains(stack, "net/http_test.interestingGoroutines") ||
			strings.Contains(stack, "runtime.MHeap_Scavenger") {
			continue
		}
		gs = append(gs, stack)
	}
	sort.Strings(gs)
	return
}

// This code is taken from: https://github.com/golang/go/blob/d82e51a11973714708ddc7f9f055ae8ea3d509f1/src/net/http/main_test.go#L30-L141
func goroutineLeaked() bool {

	var stackCount map[string]int
	for i := 0; i < 5; i++ {
		n := 0
		stackCount = make(map[string]int)
		gs := interestingGoroutines()
		for _, g := range gs {
			stackCount[g]++
			n++
		}
		if n == 0 {
			return false
		}
		// Wait for goroutines to schedule and die off:
		time.Sleep(100 * time.Millisecond)
	}
	fmt.Fprintf(os.Stderr, "Too many goroutines running.\n")
	for stack, count := range stackCount {
		fmt.Fprintf(os.Stderr, "\n\t %d instances of: %s \n\n", count, stack)
	}
	return true
}
