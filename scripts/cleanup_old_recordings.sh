#!/bin/bash

# Cleanup old recordings script
# Deletes recordings older than specified days

# Default: Delete files older than 30 days
DAYS_TO_KEEP=${1:-30}
RECORDINGS_DIR="recordings"

echo "🗑️  Cleaning up recordings older than $DAYS_TO_KEEP days..."

if [ ! -d "$RECORDINGS_DIR" ]; then
    echo "❌ Recordings directory not found: $RECORDINGS_DIR"
    exit 1
fi

# Count files before deletion
BEFORE_COUNT=$(find "$RECORDINGS_DIR" -type f | wc -l)
echo "📊 Current files: $BEFORE_COUNT"

# Delete old files
find "$RECORDINGS_DIR" -type f -mtime +$DAYS_TO_KEEP -delete

# Count files after deletion
AFTER_COUNT=$(find "$RECORDINGS_DIR" -type f | wc -l)
DELETED_COUNT=$((BEFORE_COUNT - AFTER_COUNT))

echo "✅ Deleted $DELETED_COUNT old files"
echo "📊 Remaining files: $AFTER_COUNT"

# Calculate disk space saved
if command -v du &> /dev/null; then
    DISK_USAGE=$(du -sh "$RECORDINGS_DIR" | cut -f1)
    echo "💾 Current disk usage: $DISK_USAGE"
fi

echo "Done! ✨"

