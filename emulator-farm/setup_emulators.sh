#!/bin/bash
# Emulator Farm Setup Script
# Run this on your LOCAL machine (jarvis@Jarvis-OEM)

export ANDROID_HOME=~/Android/Sdk
export PATH=$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH
export ANDROID_EMULATOR_USE_SYSTEM_LIBS=1

echo "=========================================="
echo "Marketing Manager - Emulator Farm Setup"
echo "=========================================="

# Function to start emulator and wait for boot
start_emulator() {
    local num=$1
    local port=$((5554 + (num - 1) * 2))  # 5554, 5556, 5558...
    
    echo "Starting emulator-$num on port $port..."
    
    # Start emulator in background
    emulator -avd spotify-emulator-$num \
        -port $port \
        -no-window \
        -no-audio \
        -no-boot-anim \
        -gpu swiftshader_indirect \
        &
    
    echo "Emulator $num started (port $port)"
}

# Function to wait for emulator to be ready
wait_for_emulator() {
    local port=$1
    local num=$2
    
    echo "Waiting for emulator-$num to boot..."
    
    while true; do
        result=$(adb -s emulator-$port device 2>/dev/null | grep "device" | wc -l)
        if [ "$result" -gt 0 ]; then
            echo "Emulator $num is ready!"
            return 0
        fi
        sleep 5
    done
}

# Function to install Spotify
install_spotify() {
    local port=$1
    local num=$2
    
    echo "Installing Spotify on emulator-$num..."
    adb -s emulator-$port install -r ~/Downloads/spotify-9-1-32-2083.apk
    echo "Spotify installed on emulator-$num"
}

# Main execution
echo ""
echo "Starting batch of emulators..."

# Start first 5 emulators (adjust number based on your PC's power)
for i in 1 2 3 4 5; do
    start_emulator $i
done

# Wait for all to boot
echo ""
echo "Waiting for emulators to boot (this takes 2-3 minutes)..."
sleep 180

# Install Spotify on each
echo ""
echo "Installing Spotify..."
for i in 1 2 3 4 5; do
    port=$((5554 + (i - 1) * 2))
    install_spotify $port $i
done

echo ""
echo "=========================================="
echo "Batch 1 complete!"
echo "=========================================="
echo ""
echo "To log in to Spotify on each emulator:"
echo ""
echo "emulator-5554: Account 1 - sonic001@gmail.com"
echo "emulator-5556: Account 2 - play002@gmail.com"
echo "emulator-5558: Account 3 - music003@yahoo.com"
echo "emulator-5560: Account 4 - vibe004@yahoo.com"
echo "emulator-5562: Account 5 - music005@gmail.com"
echo ""
echo "Password for all: UO%9xpyKHgqS85x#"
echo ""
echo "After logging in, run this script again to start the next batch."
