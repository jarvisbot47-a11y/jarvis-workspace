#!/usr/bin/env python3
"""Desktop automation script for RustDesk and general GUI control."""

import subprocess
import sys
import time

def run(cmd):
    """Run shell command."""
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def click(x, y):
    """Click at coordinates using xdotool."""
    run(f"xdotool mousemove {x} {y} click 1")

def type_text(text):
    """Type text."""
    run(f"xdotool type '{text}'")

def press_key(key):
    """Press a key."""
    run(f"xdotool key {key}")

def find_window(title):
    """Find window by title."""
    result = run(f"xdotool search --name '{title}'")
    return result.stdout.strip().split('\n')[0] if result.stdout else None

def activate_window(title):
    """Activate window by title."""
    wid = find_window(title)
    if wid:
        run(f"xdotool windowactivate {wid}")

def move_window(x, y):
    """Move window to position."""
    wid = find_window("RustDesk")
    if wid:
        run(f"xdotool windowmove {wid} {x} {y}")

def resize_window(w, h):
    """Resize window."""
    wid = find_window("RustDesk")
    if wid:
        run(f"xdotool windowsize {wid} {w} {h}")

def main():
    if len(sys.argv) < 2:
        print("Usage: desktop-auto.py <command> [args]")
        print("Commands:")
        print("  click <x> <y>")
        print("  type <text>")
        print("  key <key>")
        print("  find <title>")
        print("  activate <title>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "click" and len(sys.argv) == 4:
        click(int(sys.argv[2]), int(sys.argv[3]))
    elif cmd == "type" and len(sys.argv) >= 3:
        type_text(" ".join(sys.argv[2:]))
    elif cmd == "key" and len(sys.argv) == 3:
        press_key(sys.argv[2])
    elif cmd == "find" and len(sys.argv) == 3:
        wid = find_window(sys.argv[2])
        print(f"Window ID: {wid}")
    elif cmd == "activate" and len(sys.argv) == 3:
        activate_window(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()