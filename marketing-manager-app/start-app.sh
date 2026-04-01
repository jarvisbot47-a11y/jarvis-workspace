#!/bin/bash
set -e

AIO_DIR="/home/jarvis/.openclaw/workspace/aiostream-clone"
APP_DIR="/home/jarvis/.openclaw/workspace/marketing-manager-app"

# Find free port
for PORT in 5001 5002 5003 5004 5005; do
  if ! nc -z 127.0.0.1 $PORT 2>/dev/null; then
    break
  fi
done
export FLASK_URL="http://127.0.0.1:$PORT"

# Kill old processes
pkill -f "marketing-manager.*flask\|marketing-manager-flask" 2>/dev/null || true
pkill -f "electron.*marketing" 2>/dev/null || true
sleep 1

echo "Starting Flask on port $PORT..."

# Start Flask in background
cd "$AIO_DIR"
python3 << PYEOF > /tmp/mm-flask.log 2>&1 &
import sys, os, time
sys.path.insert(0, '$AIO_DIR')
from app import app
app.run(host='127.0.0.1', port=$PORT, debug=False, use_reloader=False, threaded=True)
PYEOF

FLASK_PID=$!
sleep 3

echo "Flask PID=$FLASK_PID, URL=$FLASK_URL"
echo "Launching Electron..."

# Start Electron
cd "$APP_DIR"
FLASK_URL="$FLASK_URL" ./node_modules/.bin/electron . --no-sandbox &
ELECTRON_PID=$!

echo "Electron PID=$ELECTRON_PID"

# Cleanup on exit
trap "kill $FLASK_PID $ELECTRON_PID 2>/dev/null; exit" SIGINT SIGTERM EXIT

# Wait for Electron
wait $ELECTRON_PID 2>/dev/null || true
