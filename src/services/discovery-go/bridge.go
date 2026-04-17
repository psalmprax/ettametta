package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"time"

	"github.com/google/uuid"
)

type AIBridge struct {
	PythonAPIURL string
}

func NewAIBridge() *AIBridge {
	url := os.Getenv("PYTHON_API_URL")
	if url == "" {
		url = "http://api:8000"
	}
	return &AIBridge{PythonAPIURL: url}
}

func (b *AIBridge) SendToPatternDeconstructor(candidate ScanResult) error {
	// Skip if no URL (empty result from API)
	if candidate.URL == "" {
		slog.Warn("Skipping - no results from YouTube API", slog.String("niche", candidate.Niche))
		return nil
	}

	// Generate a unique ID for the candidate
	candidateID := uuid.New().String()

	payload, _ := json.Marshal(map[string]interface{}{
		"id":            candidateID,
		"url":           candidate.URL,
		"niche":         candidate.Niche,
		"velocity":      candidate.Velocity,
		"thumbnail_url": candidate.ThumbnailURL,
		"title":         candidate.Title,
		"view_count":    candidate.ViewCount,
		"like_count":    candidate.LikeCount,
		"comment_count": candidate.CommentCount,
		"published_at":  candidate.PublishedAt,
		"platform":      candidate.Platform,
		"metadata": map[string]interface{}{
			"source":    "go-discovery",
			"timestamp": time.Now().Format(time.RFC3339),
		},
	})

	resp, err := b.sendWithRetry(payload)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("Python API returned status: %s", resp.Status)
	}

	slog.Info("Successfully sent to Python PatternDeconstructor", slog.String("niche", candidate.Niche))
	return nil
}

func (b *AIBridge) sendWithRetry(payload []byte) (*http.Response, error) {
	maxRetries := 3
	baseDelay := 100 * time.Millisecond

	var lastErr error
	for i := 0; i <= maxRetries; i++ {
		if i > 0 {
			delay := baseDelay * (1 << uint(i-1))
			slog.Warn("Retrying Python API call", slog.Int("attempt", i), slog.Duration("delay", delay))
			time.Sleep(delay)
		}

		resp, err := http.Post(fmt.Sprintf("%s/discovery/analyze", b.PythonAPIURL), "application/json", bytes.NewBuffer(payload))
		if err == nil {
			return resp, nil
		}
		lastErr = err
		slog.Error("Python API call failed", slog.Int("attempt", i+1), slog.Any("error", err))
	}
	return nil, fmt.Errorf("all retries failed: %w", lastErr)
}
