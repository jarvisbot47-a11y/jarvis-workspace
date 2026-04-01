#!/bin/bash
# Launches Flask server then opens the app
AIO_DIR="/home/jarvis/.openclaw/workspace/aiostream-clone"
APP_DIR="$(dirname "$(readlink -f "$0")")"

for PORT in 5001 5002 5003 5004 5005; do
  if ! nc -z 127.0.0.1 $PORT 2>/dev/null; then
    break
  fi
done

cd "$AIO_DIR"
python3 -c "
import sys, os
sys.path.insert(0, '$AIO_DIR')
from app import app
app.run(host='127.0.0.1', port=$PORT, debug=False, use_reloader=False, threaded=True)
" &
FLASK_PID=$!
sleep 3

FLASK_URL="http://127.0.0.1:$PORT" "$APP_DIR/marketing-manager" "$FLASK_URL" &
APP_PID=$!

trap "kill $FLASK_PID $APP_PID 2>/dev/null; exit" SIGINT SIGTERM EXIT
wait $APP_PID 2>/dev/null
