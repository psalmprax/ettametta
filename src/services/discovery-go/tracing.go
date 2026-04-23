package main

import (
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// TracingMiddleware extracts or generates a Request-ID
func TracingMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		rid := c.GetHeader("X-Request-ID")
		if rid == "" {
			rid = uuid.New().String()
		}

		// Set for the current request context
		c.Set("RequestID", rid)

		// Set in response header
		c.Header("X-Request-ID", rid)

		c.Next()
	}
}

// GetRequestID helper to retrieve the ID from gin context
func GetRequestID(c *gin.Context) string {
	if rid, exists := c.Get("RequestID"); exists {
		if ridStr, ok := rid.(string); ok {
			return ridStr
		}
	}
	return ""
}
