package main

import (
	"log"
	"os"
	"sync"

	"github.com/gin-gonic/gin"
)

// Config holds discovery service configuration
type Config struct {
	PythonAPIURL string
	MaxWorkers   int
	QueueSize    int
}

// Default config values
var defaultConfig = Config{
	PythonAPIURL: getEnv("PYTHON_API_URL", "http://api:8000"),
	MaxWorkers:   10,
	QueueSize:    100,
}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}

// DiscoveryService wraps scanner + bridge with proper logging
type DiscoveryService struct {
	scanner *Scanner
	bridge  *AIBridge
	config  Config
	wg      sync.WaitGroup
	jobs    chan ScanResult
}

// NewDiscoveryService creates a properly structured service
func NewDiscoveryService() *DiscoveryService {
	cfg := defaultConfig
	return &DiscoveryService{
		scanner: NewScanner(),
		bridge:  NewAIBridge(),
		config:  cfg,
		jobs:    make(chan ScanResult, cfg.QueueSize),
	}
}

// Start begins the bounded worker pool with proper logging
func (s *DiscoveryService) Start(workerCount int) {
	if workerCount > 0 {
		s.config.MaxWorkers = workerCount
	}

	log.Printf("[Discovery] Starting worker pool with %d workers", s.config.MaxWorkers)

	for i := 0; i < s.config.MaxWorkers; i++ {
		s.wg.Add(1)
		go func(workerID int) {
			defer s.wg.Done()
			log.Printf("[Discovery] Worker %d started", workerID)
			for job := range s.jobs {
				if err := s.bridge.SendToDeconstructor(job); err != nil {
					log.Printf("[Worker %d] Error sending to Python: %v", workerID, err)
				}
			}
		}(i)
	}
}

// ProcessNiches scans niches and broadcasts results
func (s *DiscoveryService) ProcessNiches(niches []string) []ScanResult {
	log.Printf("[Discovery] Starting multi-scan for niches: %v", niches)

	results := s.scanner.StartMultiScan(niches)
	log.Printf("[Discovery] Scan completed, got %d results", len(results))

	// Send results through bounded worker pool
	queued := 0
	for _, res := range results {
		select {
		case s.jobs <- res:
			queued++
		default:
			log.Printf("[Discovery] Queue full, dropping result: %s", res.Title)
		}
	}

	log.Printf("[Discovery] Queued %d/%d results for broadcast", queued, len(results))
	return results
}

// Close gracefully shuts down the worker pool
func (s *DiscoveryService) Close() {
	log.Println("[Discovery] Closing worker pool...")
	close(s.jobs)
	s.wg.Wait()
	log.Println("[Discovery] Worker pool closed")
}

// HealthCheck returns service health status
func (s *DiscoveryService) HealthCheck() map[string]interface{} {
	return map[string]interface{}{
		"service":    "discovery-go",
		"status":     "healthy",
		"workers":    s.config.MaxWorkers,
		"queue_size": s.config.QueueSize,
	}
}

// Global service instance
var discoverySvc = NewDiscoveryService()

func init() {
	// Start worker pool on init
	discoverySvc.Start(10)
}

// Health handler with proper structured logging
func healthHandler(c *gin.Context) {
	health := discoverySvc.HealthCheck()
	c.JSON(200, health)
}

// MultiScanHandler replaces the old scanAndBroadcast
func multiScanHandler(c *gin.Context) {
	var req struct {
		Niches []string `json:"niches"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		log.Printf("[Discovery] Invalid request: %v", err)
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}

	if len(req.Niches) == 0 {
		req.Niches = []string{"AI", "Fitness", "Motivation"}
	}

	results := discoverySvc.ProcessNiches(req.Niches)

	c.JSON(200, gin.H{
		"message": "Scan completed with bounded concurrency",
		"results": results,
		"engine":  "golang-clean-architecture",
	})
}
