# Marketing Manager - Transfer Guide

## What This Is
A self-contained Android emulator management app for account creation and automation.

## Transfer This Folder
Copy `/home/jarvis/.openclaw/workspace/marketing-manager-app/` to the new machine.

## On The New Machine

### 1. Install Android Studio
- Download from https://developer.android.com/studio
- Install and open Android Studio
- Go to **Tools → SDK Manager → SDK Tools**
- Check and install:
  - Android Emulator
  - Android SDK Platform-Tools
  - Google Play Intel x86 Atom System Image (or any Android 13 image)

### 2. Set Up AVD (Android Virtual Device)
- Go to **Tools → Device Manager → Create Device**
- Pick **Pixel 6** (or any generic device)
- Select **Android 13 (API 33)** as the system image
- Create the AVD

### 3. Install the App
```bash
# Make the binary executable
chmod +x marketing-manager

# Run it
./marketing-manager
```

### 4. The app auto-starts:
- Flask API on http://localhost:5001
- Electron window opens automatically

## How Many Emulators?
| RAM | Emulators |
|-----|-----------|
| 16GB | 3-4 |
| 32GB | 5-6 |
| 64GB | 10+ |

## App Structure
- `marketing-manager` — Electron binary (starts Flask + GUI)
- `app.py` — Flask backend (inside aiotream-clone/)
- `cloud_phones.py` — Emulator management + ADB automation
- `emulator_manager.py` — AVD lifecycle management
- `templates/cloud_phones.html` — Web UI

## If Emulator Won't Start
```bash
# Kill all emulators
pkill -9 emulator qemu

# Restart
./marketing-manager
```
