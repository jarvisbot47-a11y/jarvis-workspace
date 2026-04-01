#!/bin/bash
# Quick Start: Start 5 emulators and install Spotify

export ANDROID_HOME=~/Android/Sdk
export PATH=$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools:$PATH

echo "Starting 5 emulators and installing Spotify..."

# Start emulators 1-5
for i in 1 2 3 4 5; do
    port=$((5554 + (i - 1) * 2))
    echo "Starting emulator-$i on port $port..."
    emulator -avd spotify-emulator-$i -port $port -no-window -no-audio -no-boot-anim &
done

echo "Waiting 3 minutes for boot..."
sleep 180

# Install Spotify
echo "Installing Spotify..."
for i in 1 2 3 4 5; do
    port=$((5554 + (i - 1) * 2))
    adb -s emulator-$port install -r ~/Downloads/spotify-9-1-32-2083.apk 2>/dev/null
done

echo "Done! Log into Spotify on each emulator."
