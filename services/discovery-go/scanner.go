package main

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"os"
	"regexp"
	"strings"
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
	httpClient *http.Client
}

func NewScanner() *Scanner {
	apiKey := os.Getenv("YOUTUBE_API_KEY")
	scanner := &Scanner{
		MaxWorkers: 50,
		hasAPIKey:  apiKey != "",
		httpClient: &http.Client{
			Timeout: 10,
		},
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
		fmt.Printf("[Scanner] Warning: YOUTUBE_API_KEY not set - will use DuckDuckGo fallback\n")
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

// scanDuckDuckGo searches DuckDuckGo for trending videos in the niche
// This is a free fallback when YouTube API quota is exceeded
func (s *Scanner) scanDuckDuckGo(niche string) []ScanResult {
	fmt.Printf("[Scanner] Using DuckDuckGo fallback for: %s\n", niche)

	// Use lite.duckduckgo.com instead of html.duckduckgo.com (more reliable)
	searchURL := fmt.Sprintf("https://lite.duckduckgo.com/lite/?q=trending+%s+videos", strings.ReplaceAll(niche, " ", "+"))

	req, err := http.NewRequest("GET", searchURL, nil)
	if err != nil {
		fmt.Printf("[Scanner] DuckDuckGo request error: %v\n", err)
		return nil
	}

	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
	req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")

	resp, err := s.httpClient.Do(req)
	if err != nil {
		fmt.Printf("[Scanner] DuckDuckGo response error: %v\n", err)
		return nil
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("[Scanner] DuckDuckGo read error: %v\n", err)
		return nil
	}

	return s.parseDuckDuckGoResults(string(body), niche)
}

// parseDuckDuckGoResults parses DuckDuckGo HTML results
func (s *Scanner) parseDuckDuckGoResults(html string, niche string) []ScanResult {
	var results []ScanResult

	// Match result links and titles
	resultRegex := regexp.MustCompile(`<a class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>`)
	matches := resultRegex.FindAllStringSubmatch(html, -1)

	for i, match := range matches {
		if i >= 10 { // Limit to 10 results
			break
		}
		if len(match) >= 3 {
			url := match[1]
			title := strings.TrimSpace(match[2])

			// Skip internal DuckDuckGo links
			if strings.HasPrefix(url, "/") {
				continue
			}

			// Detect platform from URL
			platform := "Web"
			if strings.Contains(url, "youtube.com") || strings.Contains(url, "youtu.be") {
				platform = "YouTube"
			} else if strings.Contains(url, "tiktok.com") {
				platform = "TikTok"
			} else if strings.Contains(url, "instagram.com") {
				platform = "Instagram"
			} else if strings.Contains(url, "twitter.com") || strings.Contains(url, "x.com") {
				platform = "X"
			} else if strings.Contains(url, "reddit.com") {
				platform = "Reddit"
			}

			// Estimate velocity based on platform
			velocity := 0.5
			if platform == "YouTube" {
				velocity = 0.7
			}

			results = append(results, ScanResult{
				Niche:    niche,
				Velocity: velocity,
				URL:      url,
				Title:    title,
				Platform: platform,
			})
		}
	}

	fmt.Printf("[Scanner] DuckDuckGo found %d results for: %s\n", len(results), niche)
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

	// If no real results, try DuckDuckGo fallback
	if len(results) == 0 {
		fmt.Printf("[Scanner] No results from YouTube API, trying DuckDuckGo fallback...\n")
		for _, niche := range niches {
			ddgResults := s.scanDuckDuckGo(niche)
			for _, r := range ddgResults {
				results = append(results, r)
			}
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

		// If no results from YouTube, try DuckDuckGo fallback
		ddgResults := s.scanDuckDuckGo(niche)
		for _, r := range ddgResults {
			results <- r
		}
	}
}
