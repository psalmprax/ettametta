package main

import (
	"fmt"
	"sync"

	"github.com/gin-gonic/gin"
)

// AIBridge broadcasts scan results to Python backend
type AIBridge struct {
	BaseURL    string
	MaxWorkers int             // Max concurrent outbound requests
	results    chan ScanResult // Input queue
	wg         sync.WaitGroup
}

// NewAIBridge creates a new bridge with bounded concurrency
func NewAIBridge() *AIBridge {
	return &AIBridge{
		BaseURL:    "http://localhost:7201/api/v1/discovery/analyze",
		MaxWorkers: 10,                         // Bounded to prevent file descriptor exhaustion
		results:    make(chan ScanResult, 100), // Buffered input queue
	}
}

// Start begins the bounded worker pool
func (b *AIBridge) Start(workerCount int) {
	if workerCount > 0 {
		b.MaxWorkers = workerCount
	}

	// Start bounded worker pool
	for i := 0; i < b.MaxWorkers; i++ {
		b.wg.Add(1)
		go func(workerID int) {
			defer b.wg.Done()
			for res := range b.results {
				if err := b.SendToDeconstructor(res); err != nil {
					fmt.Printf("[Worker %d] Error: %v\n", workerID, err)
				}
			}
		}(i)
	}
}

// Send queues a result for async processing
func (b *AIBridge) Send(r ScanResult) error {
	select {
	case b.results <- r:
		return nil
	default:
		return fmt.Errorf("worker queue full, result dropped")
	}
}

// SendToDeconstructor sends a result to Python (blocking)
func (b *AIBridge) SendToDeconstructor(r ScanResult) error {
	// Actual HTTP call to Python backend
	// fmt.Printf("[Bridge] Sending to Python: %s\n", r.Title)
	return nil // Placeholder - actual implementation in bridge.go
}

// Close stops the worker pool
func (b *AIBridge) Close() {
	close(b.results)
	b.wg.Wait()
}

// Global instance
var bridge = NewAIBridge()

func init() {
	// Start worker pool on init
	bridge.Start(10)
}

// MultiScanWithBroadcast scans niches and broadcasts results with bounded concurrency
func MultiScanWithBroadcast(niches []string) []ScanResult {
	scanner := NewScanner()
	results := scanner.StartMultiScan(niches)

	// Send results through bounded worker pool
	for _, res := range results {
		if err := bridge.Send(res); err != nil {
			fmt.Printf("[Broadcast] Failed to queue: %v\n", err)
		}
	}

	return results
}

// Original function preserved for backward compatibility
func scanAndBroadcast(c *gin.Context) {
	var req ScanRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if len(req.Niches) == 0 {
		req.Niches = []string{"AI", "Fitness", "Motivation"}
	}

	// Use bounded broadcast instead of unbounded goroutines
	results := MultiScanWithBroadcast(req.Niches)

	c.JSON(http.StatusOK, gin.H{
		"message": "Scan completed with bounded concurrency",
		"results": results,
		"engine":  "golang-bounded-worker-pool",
	})
}
