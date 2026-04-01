---
name: browser-automation-suite
description: Comprehensive browser automation for scraping, data extraction, automated form filling, and web interaction. Use when Mystik needs to: scrape a website, extract data from pages, automate web logins, fill forms automatically, take screenshots of web content, monitor web pages for changes, or interact with web apps programmatically. Triggers on: "scrape", "extract data", "automate web", "fill form", "take screenshot of", "monitor this page", "auto-login".
---

# Browser Automation Suite

## Core Principle
Always spawn a SUBAGENT for browser tasks. Your only job: delegate, monitor, synthesize.

## Workflow

### 1. Plan
- What site/page needs interaction?
- Is it a one-time scrape or recurring task?
- Login required? (get credentials from TOOLS.md or ask Mystik)
- Output format needed?

### 2. Spawn Browser Subagent
```bash
sessions_spawn task:"<task>" runtime:"subagent" sandbox:"require" runTimeoutSeconds:600
```
Include:
- Target URL(s)
- Specific actions (click X, fill Y, extract Z, scroll to find W)
- Login details if needed
- Output destination
- Any anti-bot considerations

### 3. Monitor
- Use `process action=poll sessionId:<id> timeout:30000` to check progress
- Browser tasks can be slow - be patient (5-10 min is normal)
- If browser crashes, respawn

### 4. Deliver
- Save extracted data to workspace
- Report what was found/extracted
- Note any issues encountered

## Browser Tool Usage
Agent Browser skill is at `~/.openclaw/skills/agent-browser/SKILL.md`

Key commands:
```bash
agent-browser --headed open <url>           # Open page visible
agent-browser wait --load networkidle        # Wait for content
agent-browser --headed snapshot -i            # Get interactive snapshot
agent-browser --headed click @e<n>            # Click element
agent-browser --headed fill @e<n> "text"      # Type text
agent-browser --headed screenshot             # Screenshot
```

## Headless vs Headed
- **Headless**: Faster, no visible window, good for simple scrapes
- **Headed**: User can see what's happening, good for complex interactions
- Default to headless unless debugging or complex interactions needed
