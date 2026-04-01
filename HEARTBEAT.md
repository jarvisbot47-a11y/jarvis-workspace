# HEARTBEAT.md

# Periodic health checks for all systems

## Health Check Tasks

Run these periodically to verify all systems are operational:

### 1. Gateway Status
- Check gateway is running: `openclaw gateway status`
- Verify no errors in logs: `tail -20 /tmp/openclaw/openclaw-2026-03-23.log | grep -i error`

### 2. Voice Reply Skill
- Test edge-tts: `edge-tts --text "test" --write-media /tmp/test-tts.mp3 --voice en-GB-RyanNeural`
- Verify faster-whisper available: `python3 -c "from faster_whisper import WhisperModel; print('ok')"`

### 3. QMD Memory
- Test qmd command: `qmd --version`
- Verify QMD process not spawning infinitely: `ps aux | grep qmd | grep -v grep | wc -l` (should be 0-1)

### 4. Browser Automation
- Check chromium available: `which chromium-browser`
- (Note: agent-browser was removed due to issues - using web_fetch for now)

### 5. Disk Space
- Check workspace: `df -h /home/jarvis/.openclaw/workspace`

## Alert Conditions

If any check fails, alert the user with details.

## Frequency

Run full health check 2-3 times per day during active use periods.