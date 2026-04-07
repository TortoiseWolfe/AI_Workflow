# Priming Patterns

How to load and reload Claude's context within a session. The commands you use to say "read my rules, then shut up and wait for work."

---

## The commands

| Command | Lives in | What it does | When to use |
|---|---|---|---|
| `/prep` | `.claude/commands/prep.md` | Reads `CLAUDE.md`, outputs `Read project context. Ready.` | Start of every session |
| `/prime [role]` | `.claude/commands/prime.md` | Reads `CLAUDE.md` + role-specific file + inventory | Advanced: when you have role-based terminals (Chapter 05) |
| `/clear` | Built-in | Wipes conversation, keeps repo context | When conversation is getting long |
| `/compact` | Built-in | Summarizes and keeps summary | **Almost never** — see below |

## The `/prep` command — the 12-line gold standard

Here's the entire `/prep` command:

```markdown
---
description: Prepare to discuss this repository (non-verbose)
scope: personal
---

Read and internalize CLAUDE.md without summarizing.

## Instructions

1. Read `CLAUDE.md`
2. Do NOT summarize or explain

## Output

> "Read project context. Ready."
```

**That's it.** Twelve lines. No fluff. And it's exactly right.

**Why it's exactly right:**

1. **"Do NOT summarize or explain"** — This is the critical line. Without it, Claude reads your 200-line `CLAUDE.md` and produces a 400-token summary ("I see this is a Next.js project using..."). That summary burns context AND tells you nothing you didn't already know. The output rule prevents the waste.

2. **A single confirmation string** — `"Read project context. Ready."` is 4 words. You know the read happened. Claude is now armed. Move on.

3. **No error handling** — If `CLAUDE.md` is missing, Claude will say so. You don't need the command to handle edge cases.

4. **Scope: personal** — This is a global command, not per-repo. You want it in every project without copying.

## The flow: `/prep` every session

Here's the complete opening sequence for any work session on a repo:

```bash
cd ~/repos/my-project
docker compose up -d        # start dev env in background
claude                       # launch Claude Code
```

At the Claude prompt:

```
/prep
```

Wait for `Read project context. Ready.` Then ask your real question. **Every session.** Don't skip it. The 2 seconds of `/prep` prevents 30 minutes of Claude getting things wrong for lack of context.

## Mid-session: when context fills up

Claude Code shows a context-usage meter (usually bottom-right or in the status line). When it gets to ~70-80%, you have two choices.

### The right choice: `/clear` + `/prep`

```
/clear
```

(conversation wiped)

```
/prep
```

(`CLAUDE.md` re-read, ready)

Now continue working. You've lost the conversation history but kept the repo context. The chat starts empty but Claude still knows your project rules.

### The trap: `/compact`

`/compact` takes your conversation so far and replaces it with a summary. Sounds efficient. It's a trap. Three reasons:

**1. Compacted summaries preserve mistakes.** If Claude misread a file 40 messages ago and later corrected itself, the compacted summary often keeps the *misreading* as "a fact Claude learned about this project." You now have a broken assumption baked into the context.

**2. Compacted summaries lose file state.** Claude knew file X had contents Y five messages ago. After compact, Claude knows "file X is related to the auth flow" and has to re-read it. The re-read blows up the context just as bad as `/clear` would have — except now you also have lossy half-memories polluting the rest of the session.

**3. Compacted context is sticky.** Once you compact, the lossy summary stays for the rest of the session. A bad compact at message 50 can ruin messages 51-200.

**The war story:** TurtleWolfe debugged a compacted session where Claude kept patching a test file at `src/components/Button/Button.test.tsx`. The file had moved to `src/__tests__/Button.test.tsx` weeks earlier. The compacted summary from an older session still said "tests live alongside components" — Claude kept looking in the wrong place, getting it wrong, apologizing, and looking in the wrong place again. Three cycles. `/clear` + `/prep` would have solved it in one message.

**Rule:** `/clear` + `/prep` is almost always the right move. `/compact` is for very specific situations (long refactor discussions where you genuinely need the history, and you accept the pollution risk). If you're not sure, `/clear`.

## Advanced: role-based priming (Chapter 05 territory)

When you start running parallel terminals with assigned roles (Chapter 05), `/prep` isn't granular enough. You use `/prime [role]` instead:

```
/prime developer
/prime architect
/prime security
```

Each loads `CLAUDE.md` plus a role-specific file plus any inventory files the role needs. The full story is in [Chapter 05 — Advanced Orchestration](../05-advanced-orchestration/).

**For Day 1: ignore `/prime`. Use only `/prep`.**

## The golden rule

> Every session starts with `/prep`. Every context refill uses `/clear` + `/prep`. `/compact` is the last resort, not the first.

Live by this and you will save dozens of hours per month.

---

## Related

- [writing-claude-md.md](writing-claude-md.md) — what `/prep` actually reads
- [Chapter 05 — Advanced Orchestration](../05-advanced-orchestration/) — when `/prime [role]` matters
- [`principles/context-hygiene.md`](../principles/context-hygiene.md) — the rule with its war story
- [Chapter 03 starter kit `/prep`](../03-slash-commands/starter-kit/.claude/commands/prep.md) — the exact file to copy
