package main

import (
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

	// Use bounded broadcast instead of unbounded goroutines
	results := MultiScanWithBroadcast(req.Niches)

	c.JSON(http.StatusOK, gin.H{
		"message": "Scan completed with bounded concurrency",
		"results": results,
		"engine":  "golang-bounded-worker-pool",
	})
}
