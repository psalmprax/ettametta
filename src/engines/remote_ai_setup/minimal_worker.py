#!/usr/bin/env python3
"""
Minimal AI Worker Health Server
Provides basic health endpoint for cluster connectivity
"""

import os
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="AI Worker Health")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "busy": False,
        "current_model": "minimal",
        "hardware": {"gpu": "unknown", "cpu": "available", "memory": "available"},
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8122))
    print(f"🚀 Minimal AI Worker Health Server starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
