#!/bin/bash
# MuAPI wrapper for image/video generation

TYPE=$1
PROMPT=$2
MODEL=$3

API_KEY=$(cat ~/.openclaw/credentials/muapi.json | grep -o '"apiKey": "[^"]*"' | cut -d'"' -f4)

if [ -z "$API_KEY" ]; then
    echo "Error: No API key found"
    exit 1
fi

# Default models
if [ "$TYPE" = "image" ]; then
    MODEL="${MODEL:-nano-banana}"
    URL="https://api.muapi.ai/v1/image/generation"
    BODY="{\"prompt\": \"$PROMPT\", \"model\": \"$MODEL\"}"
elif [ "$TYPE" = "video" ]; then
    MODEL="${MODEL:-veo3.1-fast-text-to-video}"
    URL="https://api.muapi.ai/v1/video/generation"
    BODY="{\"prompt\": \"$PROMPT\", \"model\": \"$MODEL\"}"
else
    echo "Usage: $0 <image|video> <prompt> [model]"
    exit 1
fi

echo "Calling MuAPI: $TYPE with model $MODEL"
echo "Prompt: $PROMPT"

# Make the API call
curl -s -X POST "$URL" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d "$BODY" | tee /tmp/muapi-response.json

echo ""
echo "Response saved to /tmp/muapi-response.json"