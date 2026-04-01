#!/bin/bash
# Starts Flask server, then opens the app

AIO_DIR="/home/jarvis/.openclaw/workspace/aiostream-clone"
APP_DIR="/home/jarvis/.openclaw/workspace/marketing-manager-app"

# Kill old flask instances on our port range
pkill -f "python3.*marketing" 2>/dev/null
sleep 1

# Find free port
for PORT in 5001 5002 5003 5004 5005; do
  if ! nc -z 127.0.0.1 $PORT 2>/dev/null; then
    break
  fi
done

echo "Starting Flask on port $PORT..."

# Start Flask in background
cd "$AIO_DIR"
python3 -c "
import sys, os
sys.path.insert(0, '$AIO_DIR')
from app import app
app.run(host='127.0.0.1', port=$PORT, debug=False, use_reloader=False, threaded=True)
" > /tmp/marketing-manager-flask.log 2>&1 &

FLASK_PID=$!

# Wait for Flask to start
sleep 3

echo "Flask started (PID $FLASK_PID), launching Electron..."

# Start Electron with Flask URL
FLASK_URL="http://127.0.0.1:$PORT" \
  ./node_modules/.bin/electron . &

ELECTRON_PID=$!

# Wait for Electron to exit, then kill Flask
wait $ELECTRON_PID 2>/dev/null
kill $FLASK_PID 2>/dev/null
