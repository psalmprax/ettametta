#!/bin/bash
# YouTube Cookie Export Script
# This script helps export YouTube cookies for yt-dlp to bypass bot detection
#
# Usage:
#   ./scripts/export_youtube_cookies.sh
#
# Requirements:
#   - yt-cookie-extractor browser extension OR
#   - Use yt-dlp's built-in cookie extraction

set -e

COOKIES_DIR="cookies"
YOUTUBE_COOKIES="$COOKIES_DIR/youtube_cookies.txt"
TIKTOK_COOKIES="$COOKIES_DIR/tiktok_cookies.txt"

echo "=== YouTube/TikTok Cookie Export Script ==="
echo ""

# Create cookies directory if it doesn't exist
mkdir -p "$COOKIES_DIR"

# Check if cookies already exist
if [ -f "$YOUTUBE_COOKIES" ]; then
    echo "✓ YouTube cookies already exist at $YOUTUBE_COOKIES"
    echo "  Size: $(wc -c < "$YOUTUBE_COOKIES") bytes"
    echo "  Lines: $(wc -l < "$YOUTUBE_COOKIES")"
else
    echo "✗ YouTube cookies not found at $YOUTUBE_COOKIES"
fi

if [ -f "$TIKTOK_COOKIES" ]; then
    echo "✓ TikTok cookies already exist at $TIKTOK_COOKIES"
else
    echo "✗ TikTok cookies not found at $TIKTOK_COOKIES"
fi

echo ""
echo "=== How to Export Cookies ==="
echo ""
echo "Option 1: Using Chrome/Edge Extension"
echo "  1. Install 'Get cookies.txt LOCALLY' extension"
echo "  2. Go to youtube.com and tiktok.com"
echo "  3. Click the extension and export cookies as txt"
echo "  4. Save as $YOUTUBE_COOKIES and $TIKTOK_COOKIES"
echo ""
echo "Option 2: Using yt-dlp (if already logged in)"
echo "  # YouTube:"
echo "  yt-dlp --cookies-from-browser chrome > $YOUTUBE_COOKIES"
echo ""
echo "  # TikTok:"
echo "  yt-dlp --cookies-from-browser chrome > $TIKTOK_COOKIES"
echo ""
echo "Option 3: Using command line (requires logged in browser)"
echo "  # Chrome:"
echo "  yt-dlp --cookies-from-browser chrome -o $YOUTUBE_COOKIES https://youtube.com"
echo ""
echo "  # Firefox:"
echo "  yt-dlp --cookies-from-browser firefox -o $YOUTUBE_COOKIES https://youtube.com"
echo ""

# Set proper permissions
chmod 600 "$COOKIES_DIR"/*.txt 2>/dev/null || true

echo "=== Setup Complete ==="
echo ""
echo "To test cookies work, run:"
echo "  yt-dlp --cookies $YOUTUBE_COOKIES https://youtube.com/watch?v=dQw4w9WgXcQ --skip-download --simulate"
