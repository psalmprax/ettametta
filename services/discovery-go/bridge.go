package main

import (
	"bytes"
	"encoding/json"
	"fmt"
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

func (b *AIBridge) SendToDeconstructor(candidate ScanResult) error {
	// Skip if no URL (empty result from API)
	if candidate.URL == "" {
		fmt.Printf("[Bridge] Skipping %s - no results from YouTube API\n", candidate.Niche)
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
		"platform":      candidate.Platform,
		"metadata": map[string]interface{}{
			"source":    "go-discovery",
			"timestamp": time.Now().Format(time.RFC3339),
		},
	})

	resp, err := http.Post(fmt.Sprintf("%s/discovery/analyze", b.PythonAPIURL), "application/json", bytes.NewBuffer(payload))
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("Python API returned status: %s", resp.Status)
	}

	fmt.Printf("[Bridge] Successfully sent %s to Python deconstructor\n", candidate.Niche)
	return nil
}
