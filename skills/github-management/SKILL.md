---
name: github-management
description: GitHub repository management, commits, pushes, and Pages deployment workflow. Use when Mystik needs to: commit and push changes, deploy to GitHub Pages, manage repo files, sync workspace backups, or troubleshoot GitHub build issues. Triggers on: "push to github", "commit these changes", "deploy to github pages", "sync my backup", "github pages is broken", "update my repo".
---

# GitHub Management Workflow

## Core Principle
Always spawn a SUBAGENT for GitHub operations. Your only job: delegate, monitor, synthesize.

## Workflow

### 1. Plan
- What needs to be done? (push, commit, deploy, restore)
- Which repo? (check TOOLS.md for repo URLs and token info)
- Any files that changed?

### 2. Spawn GitHub Subagent
```bash
sessions_spawn task:"<task>" runtime:"subagent" sandbox:"require" runTimeoutSeconds:120
```
Include:
- Exact git commands needed
- Commit message
- Target repo and branch
- Any file paths involved

### 3. Monitor & Trigger Deploy
- For GitHub Pages: After successful push, trigger rebuild via API:
```bash
curl -s -X POST \
  -H "Authorization: token <TOKEN>" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/<owner>/<repo>/pages/builds"
```

### 4. Deliver
- Report commit SHA, deployment URL
- Note any build errors
- Confirm live URL

## GitHub Info (from TOOLS.md)
- Token: stored in `~/.openclaw/credentials/github.json`
- mystiksingh repo: `jarvisbot47-a11y/mystiksingh`
- Workspace backup: `jarvisbot47-a11y/jarvis-032426`
