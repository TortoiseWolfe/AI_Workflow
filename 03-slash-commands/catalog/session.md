# Command Catalog — Session

Commands that manage the state of your current Claude Code session — progress, stats, continuation across sessions.

None of these are in the starter kit. They're useful, not essential. Add them when you feel the specific need they address.

---

## `/session-summary` — generate a handoff prompt

**Starter kit:** YES
**Scope:** personal

Produces a "continuation prompt" you can paste at the start of a new session to pick up where you left off. Includes:
- What was being worked on
- Files recently touched
- Open questions
- Next planned action

**When it's useful:**
- You're ending a session mid-task and want to resume tomorrow
- You're about to `/clear` and want the next primed session to start with full context
- You're handing off to a teammate who'll pick up the work

**How it's different from `/compact`:**
- `/compact` tries to shrink the current session in place (with all its problems — see [priming-patterns.md](../../02-give-it-context/priming-patterns.md))
- `/session-summary` produces a **text artifact** you save externally. The current session keeps running. You paste the text into a fresh `/clear`ed session later.

---

## `/session-stats` — token and cost accounting

**Starter kit:** YES
**Scope:** personal

Shows how many tokens the current session has used, broken down by:
- Input tokens
- Output tokens
- Cached tokens
- Total cost estimate

**When it's useful:**
- You're debugging why context feels "heavy"
- You're building a budget for your work
- You want to catch a runaway loop before it's expensive

Claude Code has this built-in to a degree. The slash-command variant is a pretty formatter.

---

## `/status` — project health dashboard

**Starter kit:** YES
**Scope:** personal or project

In TurtleWolfe's workflow, `/status` is the single command that shows:
- Current git branch + uncommitted changes
- Test suite status (last run, pass/fail)
- Pending tasks from `tasks.md` (if SpecKit is in use)
- Open RFCs (if the orchestration layer is in use — Chapter 05)
- Terminal states (if the tmux assembly line is running — Chapter 05)

For a Day-1 intern, a minimal `/status` shows:
- `git status --short`
- Whether the dev server is running
- Whether tests currently pass

Add it when you find yourself typing `git status && docker compose ps && pnpm test --run` multiple times a day.

---

## `/clean-start` — restart Docker dev env from scratch

**Starter kit:** YES
**Scope:** personal

Stops the current Docker environment, removes containers and volumes, rebuilds from scratch, and starts fresh. Used when something gets stuck — stale cache, corrupt node_modules, weird permission state — and you'd rather nuke and rebuild than diagnose.

**Roughly equivalent to:**
```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

…except the command also handles the project-specific quirks (which volumes to preserve, which post-up commands to run).

**When to use:**
- Tests pass in CI but fail locally
- Hot reload stopped working
- Docker says "container not found" for a service that should exist
- You changed package.json/requirements.txt and don't trust the cached layer

**When NOT to use:**
- Mid-debug — `/clean-start` wipes the state you were debugging
- When your data is in a Docker volume and not backed up

---

## `/read-spec` — load a feature spec into context

**Starter kit:** YES
**Scope:** personal

Reads a SpecKit-style spec file (`specs/NNN-name/spec.md`) into context with a concise summary, so you can pick up work on a feature in progress without manually `cat`-ing files.

Pairs with `/read-issues` for wireframe issues files.

---

## `/read-issues` — silently load wireframe issues files

**Starter kit:** YES
**Scope:** personal

Reads all wireframe issues files (`*.issues.md`) silently, no summary output. Used when starting a wireframe-fix session — you want Claude to know what's broken without spending tokens on a summary.

(The "silent load, terse confirmation" pattern from `/prep` applied to wireframe issues.)

---

## Design principles for session commands

1. **Read-only by default.** Session commands report state. They don't mutate. If you want mutation, there's a specific command (`/commit`, `/test`, etc.).

2. **Fast.** Session commands should return in under 3 seconds. They're for checking in, not for deep analysis. Deep analysis goes in `/code-review` or similar.

3. **Consistent output format.** Pick a format (table, JSON, prose) and stick with it. When you glance at `/status` output, you should pattern-match it in under 2 seconds.

4. **One job per command.** `/session-stats` shows stats. `/session-summary` generates handoff text. `/status` shows repo health. Don't merge them into a mega-command.

---

## Related

- [priming-patterns.md](../../02-give-it-context/priming-patterns.md) — why `/session-summary` beats `/compact`
- [Chapter 05 — Advanced Orchestration](../../05-advanced-orchestration/) — where `/status` gets ambitious
