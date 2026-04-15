package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"log/slog"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
)

// AuthConfig holds authentication settings
type AuthConfig struct {
	APIKey       string
	HMACSecret   string
	AllowedIPs   string
	RateLimitRPS int
}

var authCfg = AuthConfig{
	APIKey:       os.Getenv("DISCOVERY_API_KEY"),
	HMACSecret:   os.Getenv("DISCOVERY_HMAC_SECRET"),
	AllowedIPs:   os.Getenv("DISCOVERY_ALLOWED_IPS"),
	RateLimitRPS: 10,
}

// RequireAuth middleware validates API key
func RequireAuth() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Skip if no API key configured
		if authCfg.APIKey == "" {
			slog.Warn("No API key configured - allowing all requests")
			c.Next()
			return
		}

		// Check API key header
		apiKey := c.GetHeader("X-API-Key")
		if apiKey == "" {
			// Try query param as fallback
			apiKey = c.Query("api_key")
		}

		if apiKey == "" {
			slog.Warn("Access denied: No API key provided", slog.String("ip", c.ClientIP()))
			c.JSON(http.StatusUnauthorized, gin.H{"error": "API key required"})
			c.Abort()
			return
		}

		// Validate API key (simple string match or HMAC)
		if authCfg.HMACSecret != "" {
			// HMAC validation
			expectedSig := computeHMAC(c.Request.URL.Path, authCfg.HMACSecret)
			sig := c.GetHeader("X-Signature")
			if sig == "" || !hmac.Equal([]byte(sig), []byte(expectedSig)) {
				slog.Warn("Access denied: Invalid signature", slog.String("ip", c.ClientIP()))
				c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid signature"})
				c.Abort()
				return
			}
		} else if apiKey != authCfg.APIKey {
			slog.Warn("Access denied: Invalid API key", slog.String("ip", c.ClientIP()))
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid API key"})
			c.Abort()
			return
		}

		slog.Debug("Access allowed", slog.String("ip", c.ClientIP()))
		c.Next()
	}
}

// computeHMAC creates HMAC signature for request validation
func computeHMAC(message, secret string) string {
	h := hmac.New(sha256.New, []byte(secret))
	h.Write([]byte(message))
	return hex.EncodeToString(h.Sum(nil))
}

// RateLimitMiddleware provides simple rate limiting
func RateLimitMiddleware() gin.HandlerFunc {
	// Simple token bucket implementation
	requests := make(chan time.Time, authCfg.RateLimitRPS)

	go func() {
		for {
			select {
			case <-requests:
				// Allow request through
			case <-time.After(time.Second):
				// Refill bucket
			}
		}
	}()

	return func(c *gin.Context) {
		select {
		case requests <- time.Now():
			c.Next()
		default:
			slog.Warn("Rate limit exceeded", slog.String("ip", c.ClientIP()), slog.Int("limit", authCfg.RateLimitRPS))
			c.JSON(http.StatusTooManyRequests, gin.H{"error": "Rate limit exceeded"})
			c.Abort()
		}
	}
}
