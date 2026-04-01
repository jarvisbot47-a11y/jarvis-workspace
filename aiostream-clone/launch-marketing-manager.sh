#!/bin/bash
# Launch Marketing Manager and open in browser

APP_DIR="/home/jarvis/.openclaw/workspace/aiostream-clone/dist/Marketing Manager"
APP="$APP_DIR/Marketing Manager"

# Start the app in background
"$APP" &
APP_PID=$!

# Wait for server to start
sleep 3

# Open browser
xdg-open http://127.0.0.1:5001 2>/dev/null || sensible-browser http://127.0.0.1:5001 2>/dev/null || firefox http://127.0.0.1:5001 2>/dev/null || chromium http://127.0.0.1:5001 2>/dev/null || echo "Open http://127.0.0.1:5001 in your browser"

# Wait for app to exit
wait $APP_PID
