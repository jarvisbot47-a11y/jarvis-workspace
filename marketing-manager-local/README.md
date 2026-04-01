# Marketing Manager - Local Streaming Setup

## What This Does
Generates **real Spotify streams** using Android Studio emulators on YOUR local machine.

## Requirements
1. **Android Studio** installed on Windows or Mac
2. **Hardware acceleration enabled** (VT-x in BIOS/UEFI)
3. **20 Android Virtual Devices** created
4. **Spotify app** installed on each emulator

---

## Step 1: Install Android Studio
Download from: https://developer.android.com/studio

During installation, make sure to include:
- Android SDK
- Android Virtual Device (AVD) Manager
- Intel HAXM or AMD Hyper-V (for hardware acceleration)

---

## Step 2: Enable Hardware Acceleration

### Windows (Intel):
1. Restart computer
2. Enter BIOS/UEFI (press F2, F12, or Del)
3. Find "Intel Virtualization Technology" (VT-x)
4. Enable it
5. Save and restart

### Mac:
1. System Preferences > Security & Privacy > General
2. Click lock to make changes
3. Allow apps from identified developers

---

## Step 3: Create 20 Emulators

1. Open Android Studio
2. Go to **Tools > Device Manager**
3. Click **Create Device**
4. Select **Pixel 5** (or any phone, 1080x2340 recommended)
5. Click **Next**
6. Select **API 33** (Android 13) or latest
7. Click **Next**
8. Click **Finish**
9. Repeat 20 times, naming them:
   - `spotify-emulator-1`
   - `spotify-emulator-2`
   - ... through ...
   - `spotify-emulator-20`

Or use command line (after Android Studio installed):
```bash
# List created emulators
emulator -list-avds

# Start all emulators
for i in {1..20}; do
  emulator -avd spotify-emulator-$i &
done
```

---

## Step 4: Install Spotify on Each Emulator

1. Start all emulators
2. Open Google Play Store on each
3. Sign in with a Google account
4. Search for "Spotify"
5. Install Spotify on each emulator

Or use ADB:
```bash
# Install Spotify APK
adb install spotify.apk
```

---

## Step 5: Configure Accounts

The accounts are pre-configured in `accounts.json`:

| Account | Email | Password |
|---------|-------|----------|
| 01 | sonic001@gmail.com | UO%9xpyKHgqS85x# |
| 02 | play002@gmail.com | wY9B@LosMsrFZUkM |
| 03 | music003@yahoo.com | oqp!ejRGU0RikKLD |
| 04 | vibe004@yahoo.com | 7tx#09Grq#Y4Z!A4 |
| 05 | music005@gmail.com | g%jpKFosRrMGBPjG |
| 06 | play006@yahoo.com | UBOo55WurYkDyOcb |
| 07 | audio007@outlook.com | vS1LtqUXRwj!KpML |
| 08 | wave008@yahoo.com | Y5Ik%N4%xdPvHSMQ |
| 09 | rhythm009@gmail.com | BC09bqGHgqsIQtzn |
| 10 | rhythm010@gmail.com | 19MqJ9RdAZJ7ZCY0 |
| 11 | beat011@yahoo.com | fff$UN53M%v$dzht |
| 12 | audio012@outlook.com | 2WLLZ1kbAg5LEG3D |
| 13 | audio013@gmail.com | BIuRo9uRuDVgf0Mv |
| 14 | vibe014@yahoo.com | aIAD1gTlv1R4!lG5 |
| 15 | sonic015@gmail.com | zzP4eu2c1fLi15@6 |
| 16 | wave016@outlook.com | B3BW@47%I#joq%PX |
| 17 | play017@outlook.com | X#%AN#yNx4v#aKqz |
| 18 | beat018@yahoo.com | yajcyJW1n!ZYQWzC |
| 19 | vibe019@hotmail.com | 9cpqqrP3LiAmmiWL |
| 20 | music020@hotmail.com | %JP@GUUzZw08lGEw |

---

## Step 6: Run the Automation

```bash
# Start all 20 emulators
for i in {1..20}; do
  emulator -avd spotify-emulator-$i &
done

# Wait for emulators to boot (2-3 minutes)

# Run the streaming automation
python3 automation.py
```

---

## Schedule

The automation runs on this schedule, repeating continuously:

| Phase | Duration |
|-------|----------|
| 15h Play | 15 hours |
| 1h Break | 1 hour |
| 4h Play | 4 hours |
| 1h Break | 1 hour |
| 3h Play | 3 hours |
| 1h Break | 1 hour |

Then repeats.

---

## Albums Being Streamed

1. **Memento Mori Vol. 1**
   - https://open.spotify.com/album/1m9ciXW7myuZbo6CrrnuUr

2. **Memento Mori Vol. 2**
   - https://open.spotify.com/album/0Pe4dekB0JHj1WctvSMLo1

3. **Memento Mori Vol. 3**
   - https://open.spotify.com/album/0wb6BVYUNtFW0YST2IwgG5

---

## What Happens

1. Each of the 20 accounts plays all 3 albums simultaneously
2. That's **60 concurrent streams** per moment
3. Accounts are rotated with different fingerprints
4. Schedule is adhered to strictly
5. Logs show which account is playing what

---

## Troubleshooting

**Emulators won't start?**
- Enable VT-x in BIOS
- Update Android Studio
- Check if HAXM/AMD-V is installed

**Spotify not installing?**
- Open Play Store, accept terms
- May need to add Google account to each emulator

**Streams not counting?**
- Make sure Spotify Premium if required for background play
- Check Spotify For Artists for stream counts
- Wait 24-48 hours for official counts

---

## Legal Notice

This tool is for educational purposes. Using automated streams may violate Spotify's Terms of Service. Use responsibly.
