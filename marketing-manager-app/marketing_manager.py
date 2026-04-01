#!/usr/bin/env python3
"""
Marketing Manager - Standalone Desktop App
Wraps the Flask web app in a pywebview window.
"""
import sys, os, time, socket, threading

AIO_DIR = "/home/jarvis/.openclaw/workspace/aiostream-clone"
sys.path.insert(0, AIO_DIR)

def find_free_port(start=5001):
    for port in range(start, start + 100):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('127.0.0.1', port))
            s.close()
            return port
        except OSError:
            continue
    return start

PORT = find_free_port(5001)
FLASK_URL = f"http://127.0.0.1:{PORT}"

def start_flask():
    os.chdir(AIO_DIR)
    from app import app
    app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False, threaded=True)

t = threading.Thread(target=start_flask, daemon=True)
t.start()
time.sleep(2)

import webview

window = webview.create_window(
    'Marketing Manager',
    FLASK_URL,
    width=1920,
    height=1080,
    resizable=True,
    background_color='#050210',
)

webview.start(window=window)
