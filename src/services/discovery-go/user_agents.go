package main

import (
	"os"
	"strings"
)

// UserAgentConfig manages rotated user agents
type UserAgentConfig struct {
	Agents []string
	Index  int
}

var uaConfig UserAgentConfig

func initUserAgents() {
	// Load from environment or use default
	uaEnv := os.Getenv("ROTATING_USER_AGENTS")
	if uaEnv != "" {
		uaConfig.Agents = strings.Split(uaEnv, "|")
	} else {
		// Default production user agents
		uaConfig.Agents = []string{
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
			"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
			"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
			"Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
			"Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
		}
	}
	uaConfig.Index = 0
}

// GetNextUserAgent returns the next rotated user agent
func GetNextUserAgent() string {
	if len(uaConfig.Agents) == 0 {
		initUserAgents()
	}

	agent := uaConfig.Agents[uaConfig.Index%len(uaConfig.Agents)]
	uaConfig.Index++
	return agent
}

// GetRandomUserAgent returns a random user agent
// func GetRandomUserAgent() string {
//     if len(uaConfig.Agents) == 0 {
//         initUserAgents()
//     }
//     return uaConfig.Agents[rand.Intn(len(uaConfig.Agents))]
// }
