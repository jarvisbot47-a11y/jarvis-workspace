# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## Voice (TTS)

- **Provider**: Edge TTS (free, neural voices)
- **Default voice**: en-GB-RyanNeural (British male, neural)
- **Command**: `edge-tts --text "..." --write-media file.mp3 --voice en-GB-RyanNeural`

### Available Voices

- **en-GB-RyanNeural** - Primary (British male)
- **en-US-JennyNeural** - Alternative (US female)
- **en-US-RyanNeural** - US male variant

## Browser Automation

- **Tool**: agent-browser (npm global)
- **Default mode**: --headed (for user visibility)
- **Key rule**: NEVER close browser until user says so

### Common Commands

```bash
agent-browser --headed open <url>
agent-browser wait --load networkidle
agent-browser --headed snapshot -i
agent-browser --headed click @e1
agent-browser --headed fill @e2 "text"
agent-browser screenshot
```

## Memory Backend

- **System**: QMD (semantic search)
- **Config**: openclaw.json `memory.backend = "qmd"`
- **Command path**: `/home/jarvis/.npm-global/bin/qmd`
- **Features**: BM25 + semantic embeddings + reranking

## Discord

- **Bot token**: Stored in openclaw.json
- **Channel**: Direct messages (channel_id in context)
- **Voice support**: Receive .ogg, send .mp3

## API Keys

### UploadPost
- API Key: `7214788b14c37eff9b0f0c09357a0533cd26d97b9142dec0b3753ac97534c0f2`

### MuAPI
- API Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImphcnZpc2JvdDQ3QGdtYWlsLmNvbSIsImV4cCI6NDkyODE2NTE2MCwianRpIjoiOTgwM2Y4MjMtMzNhNy00NDI0LWIxNjYtYjc0YTFkZWI2Zjg5In0.vDCIaq5hzPIpYIxs-l2iSq5haOPxg26fC_ykoiLKc9I`

## Caprine (Facebook Messenger)

- **Location**: `/home/jarvis/.openclaw/workspace/caprine-bin/squashfs-root/`
- **Launcher**: `/home/jarvis/.openclaw/workspace/caprine-bin/caprine-launcher.sh`
- **Note**: Running directly on local machine (not SSH). Display is available (:1).

## Business — Mystik Wrapz

- **Website:** https://mystikwrapz.com
- **Pricing data:** `/home/jarvis/.openclaw/workspace/mystik-wrapz-pricing.md`
- **Phone:** 213-537-4795
- **Location:** 17623 Interurban Blvd Snohomish, WA 98296
- **Services:** Vinyl Wrap, PPF, Plasti Dip, Chrome Delete, Tint, Wheels, Motorcycles

## LibreOffice

- **Location**: `/usr/bin/libreoffice`
- **Version**: 7.3.7.2
- **Components**:
  - Writer (documents .odt, .docx)
  - Calc (spreadsheets .ods, .xlsx)
  - Impress (presentations .odp, .pptx)
  - Draw (graphics .odg)
  - Base (databases)

### Usage Examples

```bash
# Convert document to PDF
libreoffice --headless --convert-to pdf file.docx

# Convert to different format
libreoffice --headless --convert-to odt file.docx
libreoffice --headless --convert-to xlsx file.csv

# Open document for editing
libreoffice --writer file.odt
libreoffice --calc file.ods

# Export to PDF
libreoffice --headless --convert-to pdf --outdir /tmp/ file.odt
```

---

Add whatever helps you do your job. This is your cheat sheet.