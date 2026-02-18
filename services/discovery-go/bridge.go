package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"
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
	payload, _ := json.Marshal(map[string]interface{}{
		"url":      candidate.URL,
		"niche":    candidate.Niche,
		"velocity": candidate.Velocity,
		"metadata": map[string]interface{}{
			"source":    "go-discovery-os",
			"timestamp": time.Now().Format(time.RFC3339),
			"os_tier":   "free",
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
