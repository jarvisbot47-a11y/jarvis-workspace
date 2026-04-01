#!/bin/bash
# Emulator Control - Simple commands to control the Android emulator

ADB="/home/jarvis/android-sdk/platform-tools/adb"
SERIAL="emulator-5554"

case "$1" in
  shell)
    $ADB -s $SERIAL shell "${@:2}"
    ;;
  tap)
    $ADB -s $SERIAL shell "input tap $2 $3"
    ;;
  swipe)
    $ADB -s $SERIAL shell "input swipe $2 $3 $4 $5"
    ;;
  text)
    $ADB -s $SERIAL shell "input text '$2'"
    ;;
  key)
    $ADB -s $SERIAL shell "input keyevent $2"
    ;;
  launch)
    $ADB -s $SERIAL shell am start -n "$2"
    ;;
  screenshot)
    $ADB -s $SERIAL shell screencap -p /sdcard/screen.png
    $ADB -s $SERIAL pull /sdcard/screen.png "$2"
    ;;
  apps)
    $ADB -s $SERIAL shell "pm list packages" | sed 's/package://'
    ;;
  status)
    echo "=== Emulator Status ==="
    $ADB devices | grep $SERIAL
    echo "=== Current App ==="
    $ADB -s $SERIAL shell "dumpsys activity activities" 2>/dev/null | grep "topResumedActivity" | head -1
    ;;
  start-spotify)
    $ADB -s $SERIAL shell am start -n com.spotify.music/.MainActivity
    ;;
  *)
    echo "Usage: emulator-control.sh {shell|tap|swipe|text|key|launch|screenshot|apps|status|start-spotify}"
    echo "Examples:"
    echo "  emulator-control.sh status"
    echo "  emulator-control.sh tap 540 800"
    echo "  emulator-control.sh text 'hello@example.com'"
    echo "  emulator-control.sh key BACK"
    echo "  emulator-control.sh screenshot /tmp/screen.png"
    echo "  emulator-control.sh launch com.spotify.music/.MainActivity"
    ;;
esac
