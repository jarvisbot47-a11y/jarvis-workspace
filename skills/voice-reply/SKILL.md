---
name: voice-reply
description: Automatic voice response system that listens to voice messages and replies with synthesized voice. Use when user sends audio (.ogg) files that need transcription and voice reply via Edge TTS with Ryan Neural voice.
---

# Voice Reply Skill

This skill enables two-way voice communication: receives voice messages, transcribes them, generates a TTS response, and sends it back to the channel.

## Workflow

1. **Detect incoming voice**: User sends an .ogg audio file (Discord voice message)
2. **Convert & transcribe**: 
   - Convert OGG to WAV (16kHz mono) using ffmpeg
   - Transcribe using faster-whisper (base model)
3. **Process request**: Parse transcription and generate appropriate response
4. **Generate voice**: Create TTS audio using Edge TTS with en-GB-RyanNeural voice
5. **Send reply**: Upload audio file to Discord channel

## Scripts

### voice-reply.sh

Main script for processing voice → reply pipeline.

```bash
# Usage: voice-reply.sh <input.ogg> <output.mp3> <text-to-speak>
./scripts/voice-reply.sh input.ogg output.mp3 "Hello, this is my response."
```

## Tools Required

- `ffmpeg` - Audio conversion
- `faster-whisper` - Speech-to-text (`pip install faster-whisper`)
- `edge-tts` - Text-to-speech (`pip install edge-tts`)

## Configuration

- Voice: **en-GB-RyanNeural** (British male, neural)
- Input format: OGG (Opus), Discord voice messages
- Output format: MP3
- Transcription: Whisper base (int8, CPU)

## Usage

When you receive an .ogg file from the user:
1. Run the voice reply pipeline
2. Extract transcription for your response
3. Send the generated MP3 back to the channel

The skill maintains full duplex voice communication - user speaks, you respond with voice.