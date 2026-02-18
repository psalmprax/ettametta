package main

import (
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	r := gin.Default()

	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "healthy",
			"service": "discovery-go",
		})
	})

	// Discovery Routes
	r.POST("/scan", scanHandler)

	log.Printf("Discovery Engine (Go) starting on port %s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to run server: %v", err)
	}
}

func scanHandler(c *gin.Context) {
	var req struct {
		Niches []string `json:"niches"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	if len(req.Niches) == 0 {
		req.Niches = []string{"AI", "Fitness", "Motivation"}
	}

	scanner := NewScanner()
	results := scanner.StartMultiScan(req.Niches)

	bridge := NewAIBridge()
	for _, res := range results {
		go func(r ScanResult) {
			if err := bridge.SendToDeconstructor(r); err != nil {
				fmt.Printf("[Bridge] Error sending to Python: %v\n", err)
			}
		}(res)
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Concurrent scan completed and sent to AI pipeline",
		"results": results,
		"engine":  "golang-concurrency",
	})
}
