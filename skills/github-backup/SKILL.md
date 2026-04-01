---
name: github-backup
description: "Backup workspace to private GitHub repo. Use when user wants to save all config, skills, and memory to GitHub for safe keeping."
---

# GitHub Backup Skill

Backup your OpenClaw workspace to a private GitHub repository.

## Setup

- Token: `~/.openclaw/credentials/github.json`
- Repo: `https://github.com/jarvisbot47-a11y/jarvis-032426.git`
- Branch: `master`

## Usage

### Manual Backup
```bash
./scripts/backup.sh
```

### What Gets Backed Up
- `SOUL.md`, `AGENTS.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`
- `skills/` - All skill folders
- `hooks/` - Automation hooks
- `memory/` - Daily memory files

### What's Ignored
- `*.mp3`, `*.wav`, `*.ogg` - Audio files
- `*.log` - Log files
- `credentials/` - API keys (kept local)
- `node_modules/`, `cache/` - Cache

## Git Commands Used
```bash
git add -A
git commit -m "Backup $(date)"
git push origin master
```

## Automatic Backup

Add to HEARTBEAT.md for periodic backups:
```bash
# Add to heartbeat checks
cd ~/.openclaw/workspace && git add -A && git commit -m "Auto-backup $(date)" && git push
```

## Verify Backup

Check GitHub repo to confirm files are uploaded.