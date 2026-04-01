#!/bin/bash
# Install Spotify on all 20 emulators - one by one
# Run with: bash ~/Downloads/install_all.sh

export ANDROID_HOME=/home/jarvis/android-sdk
export ANDROID_SDK_ROOT=/home/jarvis/android-sdk
export PATH=$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH

APK="$HOME/Downloads/spotify-9-1-32-2083.apk"

echo "============================================"
echo "Installing Spotify on all 20 emulators"
echo "============================================"
echo ""

for i in $(seq 1 20); do
    echo "=== EMULATOR $i ==="
    
    # Kill any existing emulator process
    pkill -f "emulator.*spotify-emulator-$i" 2>/dev/null
    sleep 2
    
    # Start emulator
    echo "Starting emulator-$i..."
    emulator -avd spotify-emulator-$i -no-window &
    EMULATOR_PID=$!
    
    # Wait for boot
    echo "Waiting for boot (2 minutes)..."
    sleep 120
    
    # Check if APK exists
    if [ ! -f "$APK" ]; then
        echo "ERROR: Spotify APK not found at $APK"
        kill $EMULATOR_PID 2>/dev/null
        exit 1
    fi
    
    # Install Spotify
    echo "Installing Spotify..."
    adb install -r "$APK"
    
    # Kill emulator
    echo "Killing emulator-$i..."
    pkill -f "emulator.*spotify-emulator-$i" 2>/dev/null
    kill $EMULATOR_PID 2>/dev/null
    sleep 2
    
    echo "Emulator $i complete!"
    echo ""
done

echo "============================================"
echo "ALL 20 EMULATORS HAVE SPOTIFY INSTALLED!"
echo "============================================"
