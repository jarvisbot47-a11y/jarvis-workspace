#!/bin/bash
# GitHub Backup Script

REPO_DIR="/home/jarvis/.openclaw/workspace"
GIT_TOKEN=$(cat ~/.openclaw/credentials/github.json | grep -o '"token": "[^"]*"' | cut -d'"' -f4)
REPO_URL="https://github.com/jarvisbot47-a11y/jarvis-032426.git"

echo "=== GitHub Backup Started ==="
cd "$REPO_DIR"

# Add all changes
echo "Adding files..."
git add -A

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "No changes to commit"
else
    # Commit with timestamp
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
    echo "Committing: $TIMESTAMP"
    git commit -m "Backup $TIMESTAMP"
    
    # Push with token
    echo "Pushing to GitHub..."
    git remote set-url origin "https://jarvisbot47-a11y:$GIT_TOKEN@github.com/jarvisbot47-a11y/jarvis-032426.git"
    git push origin master
    
    echo "=== Backup Complete! ==="
fi
