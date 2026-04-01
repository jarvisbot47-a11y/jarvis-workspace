---
name: content-creation
description: Content creation and publishing workflow for social media, blog posts, and marketing materials. Use when Mystik needs to: create social media posts, write captions, generate content ideas, plan content calendars, or prepare promotional materials. Triggers on: "create a post", "write a caption", "content idea", "plan my content", "make a content calendar", "generate promotional text".
---

# Content Creation Workflow

## Core Principle
Always spawn a SUBAGENT for content creation tasks. Your only job: delegate, monitor, synthesize.

## Workflow

### 1. Brief
- Platform? (Instagram, TikTok, YouTube, Twitter, etc.)
- Purpose? (promote release, engage fans, announce tour)
- Tone? (professional, casual, hype, introspective)
- Include any specific info about the release/event

### 2. Spawn Content Subagent
```bash
sessions_spawn task:"<task>" runtime:"subagent" sandbox:"require" runTimeoutSeconds:180
```
Include:
- Platform and format
- Key message/call to action
- Hashtags to include (Mystik's: #MementoMori, #MystikSingh)
- Any assets to reference

### 3. Create Options
- Generate 2-3 variations
- Vary the hook/angle
- Include suggested hashtags
- Include posting time recommendations

### 4. Deliver
- Present options clearly
- Note which performs best for that platform
- Ask if revisions needed

## Platform Best Practices
- **Instagram**: Visual-first, 150-300 chars for caption, 8-12 hashtags
- **TikTok**: Hook in first 2 seconds, trend-aware, 60-100 chars
- **Twitter/X**: Punchy, <280 chars, 2-4 hashtags
- **YouTube**: SEO-optimized title, description with timestamps
