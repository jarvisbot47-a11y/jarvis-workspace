---
name: muapi
description: "Generate images and videos using MuAPI AI platform."
---

# MuAPI Skill

**Status:** API key and JWT token saved. Ready to use.

## Credentials

- **API Key (hex):** `7214788b14c37eff9b0f0c09357a0533cd26d97b9142dec0b3753ac97534c0f2`
- **JWT Token:** Stored in `~/.openclaw/credentials/muapi.json`
- **Auth email:** jarvisbot47@gmail.com

## Authentication

JWT token available in `~/.openclaw/credentials/muapi.json`. Use `Authorization: Bearer <jwt_token>` header.

## Available Models

**Image:**
- nano-banana
- midjourney-v7
- flux-kontext-pro

**Video:**
- veo3.1-text-to-video
- sora-2

## Usage

```bash
curl -X POST https://api.muapi.ai/v1/generate \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"model": "nano-banana", "prompt": "a cat"}'
```

## Endpoint

- Base URL: `https://api.muapi.ai/v1`
- JWT expiry: 2026 (from token)

## Testing

When Mystik asks to generate something, test the API and report back on whether it works.
