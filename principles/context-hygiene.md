# Principle — Context Hygiene

> **Rule:** Every session starts with `/prep`. Every context refill uses `/clear` + `/prep`. Never `/compact`.

---

## Why

### The war story

A long debug session on ScriptHammer. Developer asked Claude to fix a failing test in `Button.test.tsx`. After 40 messages of back-and-forth — Claude reading files, proposing edits, the developer correcting, Claude trying again — the context was getting heavy. Developer ran `/compact` to make room.

`/compact` summarized the conversation. The summary said, in part:

> "The user is debugging a failing test in `src/components/Button/Button.test.tsx`. Tests in this project live alongside their components in the same directory."

That summary got kept in context. The conversation kept going. Two days later, the developer was on a different feature and ran `/test`. Three Button tests failed. Developer asked Claude to fix them.

Claude went to `src/components/Button/Button.test.tsx`. **The file didn't exist anymore.** It had been refactored a week earlier into `src/__tests__/components/Button.test.tsx` — the project had moved tests to a centralized `__tests__/` directory.

Claude:
1. Tried to read `src/components/Button/Button.test.tsx` → ENOENT
2. Searched for "Button.test" → found the new path
3. Read the new file
4. Proposed a fix that touched the new path
5. Then immediately tried to read `src/components/Button/Button.test.tsx` again to verify → ENOENT
6. Searched again, found the new path again, tried to read it
7. Got confused, asked the developer "where is the test file?"
8. Developer pointed at the new path
9. Claude said "I'll update CLAUDE.md to note the new test location"
10. Claude then proposed an edit to `src/components/Button/Button.test.tsx` again

Three loops of the same dance. The compacted summary from two days earlier — "tests live alongside their components" — was *still in context*, and it kept overriding what Claude was actually seeing in the filesystem.

The fix took 15 minutes. The fix without the bad summary in context would have taken 90 seconds. The compaction "saved" maybe 200 tokens at the time and cost an hour of debugging when it bit later.

**The lesson:** `/compact` keeps lossy summaries that pollute future reasoning. The "convenient" preservation of context is the trap.

The real fix in this case: `/clear` + `/prep`. Wipe the conversation. Re-read `CLAUDE.md`. Start fresh. The 30 seconds spent re-priming is dwarfed by the hours spent debugging poisoned context.

### The general principle

LLM context is a **lossy buffer**. Every token in your context is a token Claude has to consider on every response. Old, stale, or wrong context **persists silently** and **steers reasoning subtly** in ways that are hard to debug.

There are three ways to manage context:

1. **`/clear`** — wipes everything. Cheap. Fast. Clean. Loses nothing important because anything important is in the files.

2. **`/compact`** — replaces the conversation with a summary. **Dangerous.** Summaries are lossy. They preserve mistakes. They drop file state. They survive across phases of work and corrupt later reasoning.

3. **Do nothing** — let context grow until you hit the limit, then Claude starts dropping turns from the beginning. Worst of all worlds: unpredictable.

The right move is almost always (1). Wipe and re-prime. The cost is 30 seconds; the benefit is reasoning that operates on current truth instead of stale summaries.

---

## How to apply

### The rules

1. **Every session starts with `/prep`.** No exceptions.
   ```
   /prep
   ```
   Output: `Read project context. Ready.`
   You're now armed with current `CLAUDE.md`.

2. **When context gets heavy, `/clear` + `/prep`.**
   ```
   /clear
   /prep
   ```
   The conversation is gone. The repo context is fresh. Continue working.

3. **`/compact` is the last resort, not the first.** Reach for it only when you have a *specific* reason — usually a long architectural discussion you genuinely need to preserve. Accept the pollution risk.

4. **Watch for the warning signs that context is poisoned:**
   - Claude proposes edits to files that don't exist (or don't exist anymore)
   - Claude references "earlier we discussed X" when X was wrong or outdated
   - Claude keeps making the same mistake after you correct it
   - Claude's suggestions don't match the current code
   - Claude says "as I mentioned" about something it didn't actually mention
   - Each of these is a signal: **`/clear` and re-prime**.

5. **Re-prime after big code changes.** If you've refactored the project structure, run `/clear` + `/prep` so Claude reloads the new `CLAUDE.md`.

6. **Use `/session-summary` instead of `/compact` for handoffs.** `/session-summary` produces an *external* artifact you save outside Claude. The current session keeps running. You paste the summary into a fresh `/clear`ed session later. Same goal, no in-context pollution.

### What `/prep` actually does

`/prep` is 12 lines. The whole command:

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

The "do not summarize" line is the entire point. Without it, Claude reads `CLAUDE.md` and produces 400 tokens of "I see this is a Next.js project using..." which is wasted context.

The terse confirmation (`Read project context. Ready.`) tells you the read happened. You don't need more.

### Multi-terminal projects (Chapter 05)

If you're running the assembly line, replace `/prep` with `/prime [role]`. Same idea — load the project context plus the role-specific context, with terse confirmation. See [`02-give-it-context/priming-patterns.md`](../02-give-it-context/priming-patterns.md).

---

## When this matters most

- **Long debug sessions.** The longer the session, the more old context accumulates, the more it can poison new reasoning. `/clear` aggressively.
- **Sessions that span days.** If you come back to work after a day off, the old context is stale even if you didn't `/clear`. Re-prime.
- **After refactors.** Your `CLAUDE.md` may have been updated. Old context is now wrong. Re-prime.
- **When Claude is making mistakes you've already corrected.** Symptom of poisoned context. Wipe and try again.

---

## Related

- [`02-give-it-context/priming-patterns.md`](../02-give-it-context/priming-patterns.md) — the longer story with concrete patterns
- [`02-give-it-context/writing-claude-md.md`](../02-give-it-context/writing-claude-md.md) — what `/prep` actually reads
- [`03-slash-commands/catalog/priming.md`](../03-slash-commands/catalog/priming.md) — `/prep` and `/prime` reference
- [`03-slash-commands/starter-kit/.claude/commands/prep.md`](../03-slash-commands/starter-kit/.claude/commands/prep.md) — the command file
