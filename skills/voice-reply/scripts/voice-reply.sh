#!/bin/bash
# Voice reply script - processes voice input and sends TTS response

# Args: $1 = input ogg file, $2 = output mp3 file, $3 = text to speak

INPUT_OGG="$1"
OUTPUT_MP3="$2"
SPEAK_TEXT="$3"

# Convert OGG to WAV for Whisper
WAV_FILE="/tmp/voice-input-$$-$(date +%s).wav"

# Convert
ffmpeg -i "$INPUT_OGG" -ar 16000 -ac 1 "$WAV_FILE" -y 2>/dev/null

# Transcribe
TRANSCRIPTION=$(python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('base', device='cpu', compute_type='int8')
segments, info = model.transcribe('$WAV_FILE')
for segment in segments:
    print(segment.text, end='')
" 2>/dev/null)

# Clean up WAV
rm -f "$WAV_FILE"

# Generate TTS
edge-tts --text "$SPEAK_TEXT" --write-media "$OUTPUT_MP3" --voice en-GB-RyanNeural 2>/dev/null

echo "$TRANSCRIPTION"