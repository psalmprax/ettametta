#!/bin/bash
# Automated cleanup script for temp video files
# This script removes old video files from the temp directory to free up disk space
# Should be run via cron or similar scheduling mechanism

set -e

# Configuration
TEMP_DIR="${1:-/root/ettametta/temp}"
MAX_AGE_DAYS="${2:-1}"  # Files older than this many days will be deleted
MIN_FREE_SPACE_GB="${3:-5}"  # Minimum free space to maintain in GB

# Log file
LOG_FILE="/var/log/ettametta-cleanup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "Starting temp file cleanup..."
log "Temp directory: $TEMP_DIR"
log "Max age: $MAX_AGE_DAYS days"
log "Min free space: $MIN_FREE_SPACE_GB GB"

# Check if temp directory exists
if [ ! -d "$TEMP_DIR" ]; then
    log "ERROR: Temp directory $TEMP_DIR does not exist"
    exit 1
fi

# Get current disk usage
df_output=$(df -BG "$TEMP_DIR" | tail -1)
current_free=$(echo "$df_output" | awk '{print $4}' | sed 's/G//')
log "Current free space: ${current_free}GB"

# Remove old video files
log "Removing video files older than $MAX_AGE_DAYS days..."
old_files=$(find "$TEMP_DIR" -type f -name "*.mp4" -mtime +"$MAX_AGE_DAYS" 2>/dev/null || true)
old_count=$(echo "$old_files" | grep -c "^" || echo 0)

if [ -n "$old_files" ]; then
    # Calculate size of files to be deleted
    old_size=$(du -ch $old_files 2>/dev/null | tail -1 | cut -f1)
    log "Found $old_count old video files totaling approximately $old_size"
    
    # Delete the files
    echo "$old_files" | xargs rm -f 2>/dev/null || true
    log "Deleted $old_count old video files"
else
    log "No old video files found"
fi

# Also clean up old JSON prop files (can accumulate over time)
log "Removing old JSON prop files..."
json_count=$(find "$TEMP_DIR" -type f -name "*.json" -mtime +"$MAX_AGE_DAYS" 2>/dev/null | wc -l)
find "$TEMP_DIR" -type f -name "*.json" -mtime +"$MAX_AGE_DAYS" -delete 2>/dev/null || true
if [ "$json_count" -gt 0 ]; then
    log "Deleted $json_count old JSON files"
fi

# Check if we need to do aggressive cleanup due to low disk space
if [ "$current_free" -lt "$MIN_FREE_SPACE_GB" ]; then
    log "WARNING: Free space is below minimum threshold. Performing aggressive cleanup..."
    
    # Remove all video files older than 1 hour
    aggressive_count=$(find "$TEMP_DIR" -type f -name "*.mp4" -mmin +60 2>/dev/null | wc -l)
    find "$TEMP_DIR" -type f -name "*.mp4" -mmin +60 -delete 2>/dev/null || true
    log "Aggressively deleted $aggressive_count more video files (older than 1 hour)"
fi

# Final disk usage report
final_free=$(df -BG "$TEMP_DIR" | tail -1 | awk '{print $4}' | sed 's/G//')
log "Final free space: ${final_free}GB (was ${current_free}GB)"

if [ "$final_free" -gt "$current_free" ]; then
    freed=$((final_free - current_free))
    log "Successfully freed approximately ${freed}GB"
else
    log "No significant space freed in this run"
fi

log "Cleanup completed"
echo ""