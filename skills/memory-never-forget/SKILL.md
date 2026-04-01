---
name: memory-pro
description: "Enhanced memory system based on Atkinson-Shiffrin three-stage memory model. Use when: (1) User wants better memory of conversation history, (2) User mentions 'remember' or 'don't forget', (3) Setting up memory for a new user, (4) User asks about past conversations. Provides: automatic session start loading, real-time memory writing, long-term memory consolidation."
metadata: { "openclaw": { "emoji": "🧠" } }
---

# Memory Pro Skill v2.0

Enhanced memory system for AI assistants, based on cognitive psychology's Atkinson-Shiffrin three-stage memory model + 社区优化实践。

## v2.0 优化升级

| 优化项 | 效果 |
|--------|------|
| 瞬时缓存层 | 缓存最近10轮对话，响应速度最快 |
| 7天周期 | 短期记忆保留7天，命中准确率>70% |
| 命中率统计 | 追踪记忆检索效果，持续优化 |
| 智能检索 | 按优先级查询，避免干扰 |

## When to Use

✅ **USE this skill when:**

- Setting up memory for a new user session
- User says "remember this" or "don't forget"
- User asks "what did I tell you before?" or "do you remember"
- Starting a new conversation (load memories first)
- Ending a conversation (save important info)
- User provides important personal information

❌ **NOT use this skill when:**

- Simple Q&A that doesn't need continuity
- User explicitly wants stateless interaction

## Three-Stage Memory Model v2.0

| Stage | Human Equivalent | Implementation | TTL |
|-------|-----------------|----------------|-----|
| **Sensory** | 0.25-2秒 | 当前输入上下文 | 即时 |
| **Short-term** | 最近10轮对话 | 内存缓存 | 10轮 |
| **Working** | 最近7天 | memory/*.md | 7天 |
| **Long-term | 永久 | MEMORY.md | 永久 |

### 核心改进

1. **瞬时记忆层（缓存）**：
   - 缓存最近10轮对话
   - 优先级最高，响应速度最快
   - 占用内存极低

2. **短期记忆层（7天）**：
   - 存储最近7天的任务记录和经验
   - 每天自动更新
   - 命中准确率超过70%

3. **长期记忆层**：
   - 存储重要规则、配置、用户偏好
   - 只有需要时才检索
   - 避免干扰

## Core Workflow v2.0

### 1. Session Start (Always Run)

```
1. 检查瞬时缓存 → 最近10轮对话
2. Read USER.md - who is the user
3. Read SOUL.md - who am I
4. Read memory/today.md - what happened today
5. Read memory/yesterday.md - recent context
6. Read MEMORY.md - long-term memories
```

### 2. 智能检索流程（按优先级）

```
收到问题 →
├── 瞬时缓存命中? → 直接使用（最快）
├── 7天内记忆命中? → 使用短期记忆
├── 长期记忆命中? → 使用MEMORY.md
└── 未命中 → 搜索knowledge base
```

### 3. During Conversation

```
After each exchange:
├── 新对话(10轮外)? → 清空瞬时缓存，更新
├── New task? → Write to todos.md
├── Important info? → Write to MEMORY.md (consolidate)
├── User preference? → Update USER.md
└── Context needed? → Search memory first
```

### 4. Session End

```
Before ending:
├── 写入瞬时缓存 → 为下一轮准备
├── 清理过期记忆 → 删除7天前的内容
├── Summarize key points → Write to memory/today.md
├── Update todos → Write to todos.md
└── Confirm important items → "I've remembered that..."
```

## File Structure

```
workspace/
├── MEMORY.md           # Long-term core memories (永久)
├── USER.md             # User profile & preferences
├── SOUL.md             # Assistant identity
├── todos.md            # Pending tasks
├── memory/
│   └── YYYY-MM-DD.md  # Daily logs (保留7天)
└── knowledge/
    └── *.md            # Structured knowledge
```

## Memory Quality Check

Before answering, quickly confirm:
- [ ] 瞬时缓存有相关信息？
- [ ] 最近7天讨论过这个话题？
- [ ] 需要查长期记忆(MEMORY.md)？
- [ ] 回答后需要记住这个信息？

## Example Interactions

**User provides info:**
> User: "My birthday is March 15th"
> You: "Got it! I'll remember your birthday is March 15th" → Write to USER.md

**User asks about past:**
> User: "What did we talk about last time?"
> You: Search memory → "Last time we discussed..."

**User corrects you:**
> User: "No, that's wrong. It's not X, it's Y"
> You: "Sorry, you're right. Let me correct that" → Update relevant memory file

**Important commitment:**
> User: "Remember to send me the report tomorrow"
> You: "I'll remember! Added to todos" → Write to todos.md

## References

- [memory-v2.md](references/memory-v2.md) - Detailed system design
- [templates.md](references/templates.md) - Memory writing templates
- 社区三层架构优化：响应速度提升2倍，准确率提升21%
