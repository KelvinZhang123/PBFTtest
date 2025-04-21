// client.go
package main

import (
    "bufio"
    "flag"
    "fmt"
    "net"
    "os"
    "sync"
    "sync/atomic"
    "time"
)

var (
    primaryAddr string
    totalReqs   int
    concurrency int
)

func init() {
    flag.StringVar(&primaryAddr, "addr", "127.0.0.1:8001",
        "address of the PBFT primary (ip:port)")
    flag.IntVar(&totalReqs, "n", 10000,
        "total number of requests to send")
    flag.IntVar(&concurrency, "c", 10,
        "number of concurrent clients")
}

func main() {
    flag.Parse()

    // Channel to collect per‑req latencies
    latencies := make(chan time.Duration, totalReqs)
    var sentCount int32

    // Spawn worker goroutines
    var wg sync.WaitGroup
    for i := 0; i < concurrency; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            for {
                // pick next request index
                idx := int(atomic.AddInt32(&sentCount, 1)) - 1
                if idx >= totalReqs {
                    return
                }
                t0 := time.Now()
                if err := makeRequest(primaryAddr); err != nil {
                    fmt.Fprintf(os.Stderr, "req %d error: %v\n", idx, err)
                    return
                }
                latencies <- time.Since(t0)
            }
        }(i)
    }

    // Wait for all workers to finish, then close channel
    go func() {
        wg.Wait()
        close(latencies)
    }()

    // Collect stats
    var sum time.Duration
    var count int
    var latSlice []time.Duration
    for l := range latencies {
        sum += l
        count++
        latSlice = append(latSlice, l)
    }
    avg := sum / time.Duration(count)

    // Compute p95
    // (simple sort; OK for ~10K samples)
    sort.Slice(latSlice, func(i, j int) bool { return latSlice[i] < latSlice[j] })
    p95 := latSlice[int(float64(count)*0.95)]

    dur := sum / time.Duration(concurrency) // approximate test duration
    tps := float64(count) / dur.Seconds()

    fmt.Printf("Requests: %d, Concurrency: %d\n", count, concurrency)
    fmt.Printf("Throughput: %.2f tx/sec\n", tps)
    fmt.Printf("Avg latency: %v, p95 latency: %v\n", avg, p95)
}

// makeRequest connects to the PBFT server, sends one request, and waits for a reply.
// **YOU MUST adapt this** to whatever protocol simple_pbft expects.
func makeRequest(addr string) error {
    conn, err := net.Dial("tcp", addr)
    if err != nil {
        return err
    }
    defer conn.Close()

    // Example: send a one‑line "NoOp" command
    _, err = conn.Write([]byte("NoOp\n"))
    if err != nil {
        return err
    }

    // Wait for a line of response
    reader := bufio.NewReader(conn)
    _, err = reader.ReadString('\n')
    return err
}
