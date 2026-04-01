#!/bin/bash
# Marketing Manager - Standalone Desktop App
# Starts Flask server, then opens the Electron app

AIO_DIR="/home/jarvis/.openclaw/workspace/aiostream-clone"
APP_DIR="$(dirname "$(readlink -f "$0")")"

# Find free port
for PORT in 5001 5002 5003 5004 5005; do
  if ! nc -z 127.0.0.1 $PORT 2>/dev/null; then
    break
  fi
done

# Kill any existing Flask on those ports
for P in 5001 5002 5003 5004 5005; do
  fuser -k $P/tcp 2>/dev/null || true
done
sleep 1

# Start Flask
cd "$AIO_DIR"
python3 -c "
import sys; sys.path.insert(0, '$AIO_DIR')
from app import app
app.run(host='127.0.0.1', port=$PORT, debug=False, use_reloader=False, threaded=True)
" > /tmp/marketing-manager-flask.log 2>&1 &
FLASK_PID=$!
sleep 3

# Launch Electron app
FLASK_URL="http://127.0.0.1:$PORT" "$APP_DIR/marketing-manager" --no-sandbox --disable-gpu "$FLASK_URL" &
APP_PID=$!

# Cleanup on exit
trap "kill $FLASK_PID $APP_PID 2>/dev/null; exit 0" SIGINT SIGTERM EXIT
wait $APP_PID 2>/dev/null
