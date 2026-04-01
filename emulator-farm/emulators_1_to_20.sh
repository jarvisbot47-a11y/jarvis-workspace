#!/bin/bash
# Run each line one at a time for each emulator

# EMULATOR 1 - Already has Spotify installed
# Just log in with: sonic001@gmail.com / UO%9xpyKHgqS85x#
# Then kill it:
pkill -f "emulator.*spotify-emulator-1"

# EMULATOR 2
cd ~/Android/Sdk
./emulator/emulator -avd spotify-emulator-2 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 3
./emulator/emulator -avd spotify-emulator-3 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 4
./emulator/emulator -avd spotify-emulator-4 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 5
./emulator/emulator -avd spotify-emulator-5 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 6
./emulator/emulator -avd spotify-emulator-6 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 7
./emulator/emulator -avd spotify-emulator-7 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 8
./emulator/emulator -avd spotify-emulator-8 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 9
./emulator/emulator -avd spotify-emulator-9 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 10
./emulator/emulator -avd spotify-emulator-10 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 11
./emulator/emulator -avd spotify-emulator-11 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 12
./emulator/emulator -avd spotify-emulator-12 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 13
./emulator/emulator -avd spotify-emulator-13 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 14
./emulator/emulator -avd spotify-emulator-14 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 15
./emulator/emulator -avd spotify-emulator-15 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 16
./emulator/emulator -avd spotify-emulator-16 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 17
./emulator/emulator -avd spotify-emulator-17 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 18
./emulator/emulator -avd spotify-emulator-18 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 19
./emulator/emulator -avd spotify-emulator-19 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

# EMULATOR 20
./emulator/emulator -avd spotify-emulator-20 -no-window &
echo "Wait 2 minutes, then run: ./platform-tools/adb install ~/Downloads/spotify-9-1-32-2083.apk"

echo "ALL DONE!"
