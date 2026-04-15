package main

import (
	"log/slog"
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
	scanner    *Scanner
	bridge     *AIBridge
	config     Config
	wg         sync.WaitGroup
	resultChan chan ScanResult
}

// NewDiscoveryService creates a properly structured service
func NewDiscoveryService() *DiscoveryService {
	cfg := defaultConfig
	return &DiscoveryService{
		scanner:    NewScanner(),
		bridge:     NewAIBridge(),
		config:     cfg,
		resultChan: make(chan ScanResult, cfg.QueueSize),
	}
}

// Start begins the bounded worker pool with proper logging
func (s *DiscoveryService) Start(workerCount int) {
	if workerCount > 0 {
		s.config.MaxWorkers = workerCount
	}

	s.wg.Add(s.config.MaxWorkers)
	slog.Info("Starting worker pool", slog.Int("max_workers", s.config.MaxWorkers))

	for i := 1; i <= s.config.MaxWorkers; i++ {
		go func(workerID int) {
			defer s.wg.Done()
			slog.Debug("Worker started", slog.Int("worker_id", workerID))
			for res := range s.resultChan {
				if err := s.bridge.SendToDeconstructor(res); err != nil {
					slog.Error("Failed to send to Python deconstructor", slog.Int("worker_id", workerID), slog.Any("error", err))
				}
			}
		}(i)
	}
}

// StartMultiScan scans niches and broadcasts results
func (s *DiscoveryService) StartMultiScan(niches []string) []ScanResult {
	slog.Info("Starting multi-scan", slog.Any("niches", niches))

	results := s.scanner.StartMultiScan(niches)
	slog.Info("Scan completed", slog.Int("count", len(results)))

	// Send results through bounded worker pool
	queued := 0
	for _, res := range results {
		select {
		case s.resultChan <- res:
			queued++
		default:
			slog.Warn("Broadcast queue full, dropping result", slog.String("title", res.Title))
		}
	}

	slog.Info("Results queued for broadcast", slog.Int("queued", queued), slog.Int("total", len(results)))
	return results
}

// Stop gracefully shuts down the worker pool
func (s *DiscoveryService) Stop() {
	slog.Info("Closing worker pool...")
	close(s.resultChan)
	s.wg.Wait()
	slog.Info("Worker pool closed")
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
		slog.Error("Invalid scan request", slog.Any("error", err))
		c.JSON(400, gin.H{"error": "Invalid request body"})
		return
	}

	if len(req.Niches) == 0 {
		req.Niches = []string{"AI", "Fitness", "Motivation"}
	}

	results := discoverySvc.StartMultiScan(req.Niches)

	c.JSON(200, gin.H{
		"message": "Scan completed with bounded concurrency",
		"results": results,
		"engine":  "golang-clean-architecture",
	})
}
