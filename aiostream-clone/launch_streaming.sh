#!/bin/bash
export DISPLAY=:99

echo "Starting Marketing Manager Real Streaming..."
echo "============================================"
echo "Accounts: 20"
echo "Albums: Memento Mori Vol. 1, 2, 3"
echo "Schedule: 15h play -> 1h break -> 4h play -> 1h break -> 3h play -> 1h break (repeat)"
echo ""

python3 real_spotify_streaming.py
