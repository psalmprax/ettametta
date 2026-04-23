package main

import (
	"log/slog"
	"os"

	"github.com/gin-gonic/gin"
)

func main() {
	// Initialize default structured logger
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	slog.SetDefault(logger)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	r := gin.Default()
	r.Use(TracingMiddleware())

	r.GET("/health", healthHandler)

	// Use clean service handler with auth and rate limiting
	r.POST("/scan", RequireAuth(), RateLimitMiddleware(), multiScanHandler)

	slog.Info("Discovery Engine (Go) starting", slog.String("port", port))
	if err := r.Run(":" + port); err != nil {
		slog.Error("Failed to run server", slog.Any("error", err))
		os.Exit(1)
	}
}
