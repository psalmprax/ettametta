package main

import (
	"context"
	"fmt"
	"os"
	"sync"

	"google.golang.org/api/option"
	"google.golang.org/api/youtube/v3"
)

type ScanResult struct {
	Niche        string  `json:"niche"`
	Velocity     float64 `json:"velocity"`
	URL          string  `json:"url"`
	ThumbnailURL string  `json:"thumbnail_url"`
	Title        string  `json:"title"`
	ViewCount    int64   `json:"view_count"`
	Platform     string  `json:"platform"`
}

type Scanner struct {
	MaxWorkers int
	youtubeAPI *youtube.Service
	hasAPIKey  bool
}

func NewScanner() *Scanner {
	apiKey := os.Getenv("YOUTUBE_API_KEY")
	scanner := &Scanner{
		MaxWorkers: 50,
		hasAPIKey:  apiKey != "",
	}

	if apiKey != "" {
		ctx := context.Background()
		youtubeService, err := youtube.NewService(ctx, option.WithAPIKey(apiKey))
		if err != nil {
			fmt.Printf("[Scanner] Warning: Failed to initialize YouTube API: %v\n", err)
			scanner.hasAPIKey = false
		} else {
			scanner.youtubeAPI = youtubeService
			fmt.Printf("[Scanner] YouTube API initialized successfully\n")
		}
	}

	if !scanner.hasAPIKey {
		fmt.Printf("[Scanner] Warning: YOUTUBE_API_KEY not set - using fallback mode\n")
	}

	return scanner
}

// scanYouTube searches YouTube for videos matching the niche
func (s *Scanner) scanYouTube(niche string) []ScanResult {
	if !s.hasAPIKey || s.youtubeAPI == nil {
		return nil
	}

	ctx := context.Background()
	call := s.youtubeAPI.Search.List([]string{"snippet"}).
		Q(niche).
		Type("video").
		Order("relevance").
		MaxResults(5)

	response, err := call.Context(ctx).Do()
	if err != nil {
		fmt.Printf("[Scanner] YouTube search error for '%s': %v\n", niche, err)
		return nil
	}

	var results []ScanResult
	for _, item := range response.Items {
		// Get video statistics
		videoCall := s.youtubeAPI.Videos.List([]string{"statistics", "contentDetails"}).
			Id(item.Id.VideoId)
		videoResponse, err := videoCall.Context(ctx).Do()
		if err != nil {
			continue
		}

		var viewCount int64
		if len(videoResponse.Items) > 0 {
			viewCount = int64(videoResponse.Items[0].Statistics.ViewCount)
		}

		results = append(results, ScanResult{
			Niche:        niche,
			Velocity:     calculateVelocity(viewCount),
			URL:          fmt.Sprintf("https://www.youtube.com/watch?v=%s", item.Id.VideoId),
			ThumbnailURL: item.Snippet.Thumbnails.Default.Url,
			Title:        item.Snippet.Title,
			ViewCount:    viewCount,
			Platform:     "youtube",
		})
	}

	return results
}

// calculateVelocity returns a velocity score based on view count
func calculateVelocity(viewCount int64) float64 {
	// Velocity based on view count (0.0 to 1.0 scale)
	switch {
	case viewCount > 1000000:
		return 0.98
	case viewCount > 100000:
		return 0.85
	case viewCount > 10000:
		return 0.70
	case viewCount > 1000:
		return 0.50
	default:
		return 0.30
	}
}

func (s *Scanner) StartMultiScan(niches []string) []ScanResult {
	nichesChan := make(chan string, len(niches))
	resultsChan := make(chan ScanResult, len(niches)*5) // Expect up to 5 results per niche
	var wg sync.WaitGroup

	// 1. Spawn Workers
	numWorkers := s.MaxWorkers
	if len(niches) < numWorkers {
		numWorkers = len(niches)
	}

	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go s.worker(nichesChan, resultsChan, &wg)
	}

	// 2. Feed Niches
	for _, n := range niches {
		nichesChan <- n
	}
	close(nichesChan)

	// 3. Collect Results
	wg.Wait()
	close(resultsChan)

	var results []ScanResult
	for res := range resultsChan {
		results = append(results, res)
	}

	// If no real results from YouTube, generate fallback with proper error messaging
	if len(results) == 0 {
		for _, niche := range niches {
			results = append(results, ScanResult{
				Niche:    niche,
				Velocity: 0.0,
				URL:      "",
				Platform: "youtube",
			})
		}
	}

	return results
}

func (s *Scanner) worker(niches <-chan string, results chan<- ScanResult, wg *sync.WaitGroup) {
	defer wg.Done()
	for niche := range niches {
		// Try YouTube API first
		if s.hasAPIKey {
			ytResults := s.scanYouTube(niche)
			for _, r := range ytResults {
				results <- r
			}
		}

		// If no results from API, don't generate mock data
		// Just mark as scanned with no results
	}
}
