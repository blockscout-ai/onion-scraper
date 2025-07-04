#!/bin/bash
# Selective PNG Recovery Script
# Run this if you can find the trash location

echo "🔍 Searching for accessible .png files in trash..."

# Try different trash locations
TRASH_LOCATIONS=(
    "$HOME/.Trash"
    "/Volumes/*/.Trashes/$UID"
    "/.Trashes/$UID"
)

RECOVERY_DIR="$HOME/Desktop/recovered_screenshots_fast"
SKIPPED_FILES="$HOME/Desktop/skipped_corrupted_files.txt"

echo "📁 Recovery directory: $RECOVERY_DIR"
echo "📝 Skipped files log: $SKIPPED_FILES"
echo

# Clear previous skipped files log
> "$SKIPPED_FILES"

for trash_location in "${TRASH_LOCATIONS[@]}"; do
    if [ -d "$trash_location" ] 2>/dev/null; then
        echo "🔍 Checking: $trash_location"
        
        find "$trash_location" -name "*.png" 2>/dev/null | while read -r file; do
            filename=$(basename "$file")
            
            # Try to copy file, skip if it fails
            if cp "$file" "$RECOVERY_DIR/" 2>/dev/null; then
                echo "✅ Recovered: $filename"
            else
                echo "❌ Skipped (corrupted): $filename"
                echo "$filename" >> "$SKIPPED_FILES"
            fi
        done
    fi
done

echo
echo "✅ Recovery complete!"
echo "📊 Check the recovery folder and skipped files log"
