package main

import (
	"fmt"
	"sync"
	"time"
)

type ScanResult struct {
	Niche    string
	Velocity float64
	URL      string
}

func (s *Scanner) ScanNiche(niche string, results chan<- ScanResult, wg *sync.WaitGroup) {
	defer wg.Done()

	fmt.Printf("[Discovery] Starting scan for niche: %s\n", niche)

	// Simulate ultra-fast concurrent scanning
	time.Sleep(time.Duration(500+(100*len(niche))) * time.Millisecond)

	results <- ScanResult{
		Niche:    niche,
		Velocity: 0.85 + (0.1 * float64(len(niche)%5)),
		URL:      fmt.Sprintf("https://platform.com/v/%d", time.Now().UnixNano()),
	}
}

type Scanner struct{}

func NewScanner() *Scanner {
	return &Scanner{}
}

func (s *Scanner) StartMultiScan(niches []string) []ScanResult {
	var wg sync.WaitGroup
	resultsChan := make(chan ScanResult, len(niches))

	for _, n := range niches {
		wg.Add(1)
		go s.ScanNiche(n, resultsChan, &wg)
	}

	wg.Wait()
	close(resultsChan)

	var results []ScanResult
	for res := range resultsChan {
		results = append(results, res)
	}
	return results
}
