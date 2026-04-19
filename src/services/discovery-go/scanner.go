package main

import (
	"context"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/PuerkitoBio/goquery"
	"google.golang.org/api/option"
	"google.golang.org/api/youtube/v3"
)

var defaultUserAgents = []string{
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
	"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
	"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
	"Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
}

func getUserAgents() []string {
	custom := os.Getenv("DISCOVERY_USER_AGENTS")
	if custom != "" {
		return strings.Split(custom, ",")
	}
	return defaultUserAgents
}

type ScanResult struct {
	Niche        string  `json:"niche"`
	Velocity     float64 `json:"velocity"`
	URL          string  `json:"source_url"`
	ThumbnailURL string  `json:"thumbnail_url"`
	Title        string  `json:"title"`
	ViewCount    int64   `json:"view_count"`
	LikeCount    int64   `json:"like_count"`
	CommentCount int64   `json:"comment_count"`
	PublishedAt  string  `json:"published_at"`
	Platform     string  `json:"platform"`
	Category     string  `json:"category"` // video, blog, social, news, other
}

type Scanner struct {
	MaxWorkers int
	youtubeAPI *youtube.Service
	hasAPIKey  bool
	httpClient *http.Client
	userAgents []string
}

func NewScanner() *Scanner {
	apiKey := os.Getenv("YOUTUBE_API_KEY")
	scanner := &Scanner{
		MaxWorkers: 50,
		hasAPIKey:  apiKey != "",
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		userAgents: getUserAgents(),
	}

	if apiKey != "" {
		ctx := context.Background()
		youtubeService, err := youtube.NewService(ctx, option.WithAPIKey(apiKey))
		if err != nil {
			slog.Warn("Failed to initialize YouTube API", slog.Any("error", err))
			scanner.hasAPIKey = false
		} else {
			scanner.youtubeAPI = youtubeService
			slog.Info("YouTube API initialized successfully")
		}
	}

	if !scanner.hasAPIKey {
		slog.Warn("YOUTUBE_API_KEY not set - using DuckDuckGo fallback")
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
		slog.Error("YouTube search error", slog.String("niche", niche), slog.Any("error", err))
		return nil
	}

	var results []ScanResult
	for _, item := range response.Items {
		// Get video statistics
		videoCall := s.youtubeAPI.Videos.List([]string{"statistics", "contentDetails", "snippet"}).
			Id(item.Id.VideoId)
		videoResponse, err := videoCall.Context(ctx).Do()
		if err != nil {
			continue
		}

		var viewCount, likeCount, commentCount int64
		var publishedAt string
		if len(videoResponse.Items) > 0 {
			videoItem := videoResponse.Items[0]
			viewCount = int64(videoItem.Statistics.ViewCount)
			likeCount = int64(videoItem.Statistics.LikeCount)
			commentCount = int64(videoItem.Statistics.CommentCount)
			publishedAt = videoItem.Snippet.PublishedAt
		}

		results = append(results, ScanResult{
			Niche:        niche,
			Velocity:     calculateVelocity(viewCount, likeCount, commentCount, publishedAt),
			URL:          fmt.Sprintf("https://www.youtube.com/watch?v=%s", item.Id.VideoId),
			ThumbnailURL: item.Snippet.Thumbnails.Default.Url,
			Title:        item.Snippet.Title,
			ViewCount:    viewCount,
			LikeCount:    likeCount,
			CommentCount: commentCount,
			PublishedAt:  publishedAt,
			Platform:     "youtube",
			Category:     "video",
		})
	}

	return results
}

// scanDuckDuckGo searches DuckDuckGo for trending videos in the niche
// This is a free fallback when YouTube API quota is exceeded
func (s *Scanner) scanDuckDuckGo(niche string) []ScanResult {
	slog.Info("Using DuckDuckGo fallback", slog.String("niche", niche))

	// Use html.duckduckgo.com (more reliable than lite.duckduckgo.com)
	searchURL := fmt.Sprintf("https://html.duckduckgo.com/html/?q=trending+%s+videos", url.QueryEscape(niche))

	req, err := http.NewRequest("GET", searchURL, nil)
	if err != nil {
		slog.Error("DuckDuckGo request error", slog.Any("error", err))
		return nil
	}

	req.Header.Set("User-Agent", s.userAgents[time.Now().UnixNano()%int64(len(s.userAgents))])
	req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")

	resp, err := s.httpClient.Do(req)
	if err != nil {
		slog.Error("DuckDuckGo response error", slog.Any("error", err))
		return nil
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		slog.Warn("DuckDuckGo returned non-200 status", slog.Int("status", resp.StatusCode))
		return nil
	}

	return s.parseDuckDuckGoResults(resp.Body, niche)
}

// parseDuckDuckGoResults parses DuckDuckGo HTML results using goquery
func (s *Scanner) parseDuckDuckGoResults(body io.Reader, niche string) []ScanResult {
	var results []ScanResult

	doc, err := goquery.NewDocumentFromReader(body)
	if err != nil {
		slog.Error("Failed to parse DDG HTML", slog.Any("error", err))
		return nil
	}

	doc.Find(".result__a").Each(func(i int, sel *goquery.Selection) {
		if len(results) >= 10 {
			return
		}

		rawURL, exists := sel.Attr("href")
		if !exists {
			return
		}

		title := strings.TrimSpace(sel.Text())
		finalURL := rawURL

		// Resolve DuckDuckGo redirection links
		if strings.Contains(rawURL, "uddg=") {
			u, err := url.Parse(rawURL)
			if err == nil {
				actualURL := u.Query().Get("uddg")
				if actualURL != "" {
					finalURL = actualURL
				}
			}
		}

		// Skip remaining internal DuckDuckGo links
		if strings.HasPrefix(finalURL, "/") || strings.Contains(finalURL, "duckduckgo.com") && !strings.Contains(finalURL, "uddg=") {
			return
		}

		// Detect platform from URL
		platform := "Web"
		urlLower := strings.ToLower(finalURL)
		if strings.Contains(urlLower, "youtube.com") || strings.Contains(urlLower, "youtu.be") {
			platform = "YouTube"
		} else if strings.Contains(urlLower, "tiktok.com") {
			platform = "TikTok"
		} else if strings.Contains(urlLower, "instagram.com") {
			platform = "Instagram"
		} else if strings.Contains(urlLower, "twitter.com") || strings.Contains(urlLower, "x.com") {
			platform = "X"
		} else if strings.Contains(urlLower, "reddit.com") {
			platform = "Reddit"
		}

		// STRICTOR PATH VALIDATION: Ensure it's a direct video link, not a landing page
		category := classifyURL(urlLower, platform)
		if category == "skip" {
			return
		}

		// Estimate velocity based on platform
		velocity := 0.5
		if platform == "YouTube" {
			velocity = 0.7
		}

		results = append(results, ScanResult{
			Niche:    niche,
			Velocity: velocity,
			URL:      finalURL,
			Title:    title,
			Platform: platform,
			Category: category,
		})
	})

	slog.Info("DuckDuckGo scan complete", slog.Int("results", len(results)), slog.String("niche", niche))
	return results
}

// classifyURL determines the content category and platform-specific directness
func classifyURL(url string, platform string) string {
	// Common "ignore" patterns (search results, settings, etc.)
	ignorePatterns := []string{
		"/search", "/results", "/trending", "/explore", "/hashtag/",
		"/groups/", "/marketplace/", "/events/", "/settings",
	}

	for _, pattern := range ignorePatterns {
		if strings.Contains(url, pattern) {
			return "skip"
		}
	}

	// 1. VIDEOS (Highest priority)
	if platform == "YouTube" {
		if strings.Contains(url, "/shorts/") {
			return "video_short"
		}
		if strings.Contains(url, "/watch?v=") || strings.Contains(url, "youtu.be/") {
			return "video_long"
		}
		return "skip"
	}

	if platform == "TikTok" {
		if strings.Contains(url, "/video/") || strings.Contains(url, "/v/") || strings.Contains(url, "vt.tiktok.com/") {
			return "video"
		}
		return "skip"
	}

	if strings.Contains(url, "/reels/") || strings.Contains(url, "/reel/") {
		return "video_short"
	}
	if strings.Contains(url, "/watch/") || strings.Contains(url, "/videos/") {
		return "video_long"
	}

	// 2. BLOGS / ARTICLES
	blogPatterns := []string{
		"medium.com", "substack.com", "linkedin.com/pulse", "ghost.io", "wordpress.com",
		"blogger.com", "dev.to", "hashnode.com", "/blog/", "/article/", "/posts/",
	}
	for _, pattern := range blogPatterns {
		if strings.Contains(url, pattern) {
			return "blog"
		}
	}

	// 3. NEWS
	newsDomains := []string{
		"cnn.com", "bbc.com", "reuters.com", "nytimes.com", "theguardian.com",
		"news.google.com", "forbes.com", "bloomberg.com", "techcrunch.com",
	}
	for _, domain := range newsDomains {
		if strings.Contains(url, domain) {
			return "news"
		}
	}

	// 4. SOCIAL (General posts)
	if platform == "X" && strings.Contains(url, "/status/") {
		return "social"
	}
	if platform == "Reddit" && strings.Contains(url, "/comments/") {
		return "social"
	}

	// 5. OTHER (Generic page)
	if strings.Contains(url, "rumble.com/v/") {
		return "video_long"
	}
	if strings.Contains(url, "bilibili.com/video/") {
		return "video_long"
	}

	parts := strings.Split(url, "/")
	if len(parts) > 3 {
		return "other"
	}

	return "skip"
}

// calculateVelocity returns a velocity score based on view count, likes, and age
func calculateVelocity(viewCount, likeCount, commentCount int64, publishedAt string) float64 {
	if publishedAt == "" {
		// Fallback for missing time data
		switch {
		case viewCount > 1000000:
			return 0.95
		case viewCount > 100000:
			return 0.80
		default:
			return 0.50
		}
	}

	pubTime, err := time.Parse(time.RFC3339, publishedAt)
	if err != nil {
		return 0.5
	}

	hours := time.Since(pubTime).Hours()
	if hours < 1 {
		hours = 1
	}

	// 1. Views Per Hour (Normalizing: 1000 VPH = 1.0)
	vph := float64(viewCount) / hours
	vphScore := vph / 1000.0
	if vphScore > 1.0 {
		vphScore = 1.0
	}

	// 2. Engagement Rate (Normalizing: 5% = 1.0)
	engagementRate := 0.0
	if viewCount > 0 {
		engagementRate = float64(likeCount+commentCount) / float64(viewCount)
	}
	engagementScore := engagementRate / 0.05
	if engagementScore > 1.0 {
		engagementScore = 1.0
	}

	// 3. Recency Bonus
	recencyBonus := 1.0 / (1.0 + (hours / 24.0))

	// 4. Momentum Delta (Simulated Growth Acceleration)
	momentumDelta := 0.0
	if hours < 48 {
		momentumDelta = 0.2 // Solid boost for content under 2 days old
	}

	// Combined Formula: 35% VPH + 35% Engagement + 20% Momentum + 10% Recency
	score := (0.35 * vphScore) + (0.35 * engagementScore) + (0.2 * momentumDelta) + (0.1 * recencyBonus)

	if score > 0.99 {
		score = 0.99
	}
	if score < 0.1 {
		score = 0.1
	}

	return score
}

func (s *Scanner) StartMultiScan(niches []string) []ScanResult {
	nichesChan := make(chan string, len(niches))
	resultsChan := make(chan ScanResult, len(niches)*100) // Much larger buffer to prevent deadlocks
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
		slog.Warn("No results from YouTube API, trying DuckDuckGo fallback")
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
