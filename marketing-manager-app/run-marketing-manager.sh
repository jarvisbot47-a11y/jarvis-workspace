#!/bin/bash
# Marketing Manager - Standalone Desktop App
# Starts Flask server, opens in Chrome app mode

AIO_DIR="/home/jarvis/.openclaw/workspace/aiostream-clone"
CHROME_APP="/usr/bin/google-chrome"

# Kill old instance
pkill -f "python3.*marketing_manager" 2>/dev/null; sleep 1

# Change to app directory and start Flask in background
cd "$AIO_DIR"
python3 -c "
import sys, os, time, socket, threading
sys.path.insert(0, '$AIO_DIR')

def find_port(start=5001):
    for p in range(start, start+100):
        try:
            s = socket.socket()
            s.bind(('127.0.0.1', p))
            s.close()
            return p
        except: continue
    return start

PORT = find_port(5001)
print(f'PORT={PORT}', flush=True)

from app import app
app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False, threaded=True)
" &

FLASK_PID=$!
sleep 3

# Get the port (read from flask output)
PORT=$(grep -o 'PORT=[0-9]*' /tmp/flask-port.txt 2>/dev/null || echo "5001")

# Launch Chrome in app mode
"$CHROME_APP" \
  --app=http://127.0.0.1:5001 \
  --new-window \
  --user-data-dir=/tmp/marketing-manager-chrome-profile \
  --no-first-run \
  --no-default-browser-check \
  --disable-infobars \
  --disable_extensions \
  --window-size=1920,1080 \
  2>/dev/null &

# Wait for Flask
wait $FLASK_PID
