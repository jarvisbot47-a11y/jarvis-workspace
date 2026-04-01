---
name: research-workflow
description: Automated web research and information gathering workflow. Use when Mystik asks to research, investigate, look up, find information about, or gather data on any topic. Ties together browser automation, web fetching, and data processing into a repeatable SOP. Triggers on: "research", "look up", "find info on", "investigate", "gather data", "find this for me", "search for".
---

# Research Workflow

## Core Principle
Always spawn a SUBAGENT for the actual research work. Your only job: delegate, monitor, synthesize results.

## Workflow

### 1. Clarify (if needed)
If the query is vague, ask one clarifying question. If it's clear, skip to step 2.

### 2. Spawn Research Subagent
```bash
sessions_spawn task:"<research task>" runtime:"subagent" sandbox:"require" runTimeoutSeconds:300
```
Include:
- The exact research goal
- Sources to check (specific URLs, search terms, platforms)
- Output format needed (summary, list, table, report)
- Any specific angles or filters

### 3. Monitor
- Poll the subagent every 30-60s via `process action=poll sessionId:<id> timeout:30000`
- If stuck at a prompt, intervene with `process action=submit sessionId:<id> data:"y"`
- If looping/hallucinating, kill and respawn

### 4. Synthesize
When complete, deliver results in Mystik's requested format. Add context and insights beyond just what was found.

## Tool Stack (for subagents)
- **web_fetch**: Fast content extraction from URLs
- **web_search**: DuckDuckGo search  
- **exec**: Run Python scripts to process/parse data
- **image**: Analyze images during research

## Output Standards
- Give actionable intelligence, not raw dumps
- Cite sources with URLs
- Flag if information seems outdated or unreliable
