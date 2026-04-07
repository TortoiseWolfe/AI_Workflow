# Command Catalog — Priming

Commands that load context into Claude's working memory. These are the first commands you run in every session.

---

## `/prep` — the universal primer

**Starter kit:** yes (one of the 10)
**Scope:** personal (global)
**File:** [`../starter-kit/.claude/commands/prep.md`](../starter-kit/.claude/commands/prep.md)

The entire command is 12 lines. That's not a typo — it's the point.

### What it does

1. Reads `CLAUDE.md` at the repo root
2. Outputs exactly one line: `Read project context. Ready.`

That's it. No summary, no explanation, no "here's what I learned." Just the read and the confirmation.

### Why it's terse

Most users' first instinct is to have a priming command that reads the file AND summarizes it AND highlights anything important. **This is wrong.** Here's why:

1. **The summary wastes tokens.** Every word Claude generates to summarize `CLAUDE.md` is a word that could have been spent on real work. A 400-token summary of a 200-line file is 400 tokens of garbage in your context budget.

2. **You already read `CLAUDE.md`.** You wrote it. You don't need Claude to explain it to you.

3. **Summaries lie.** A summary is always lossy. If Claude summarizes "use pnpm not npm" as "uses pnpm", Claude just lost the prohibition. Later, when you ask "add a dependency", Claude says `npm install`.

4. **Verification is free.** The one-line confirmation `Read project context. Ready.` tells you the read happened. You don't need more.

**Rule:** Priming commands should confirm the action, not perform the action. The action is Claude holding the file in context. The confirmation is the output.

### When to use

- **Start of every session.** Every single one.
- **After `/clear`.** Always re-prime after clearing.
- **Never after `/compact`.** (You shouldn't be using `/compact` anyway.)

### When NOT to use

- **Mid-task.** If you're in the middle of editing a file, don't randomly re-prime. Wait until you `/clear`.
- **Before a one-off question.** If you're asking "what does this error mean" and you don't need repo-specific context, skip `/prep`. Not every conversation needs the full context load.

---

## `/prime [role]` — role-based priming (Chapter 05 territory)

**Starter kit:** YES (ships with the kit, but only useful with Chapter 05 infrastructure)
**Scope:** personal (global)

`/prime` is `/prep` on steroids — it loads `CLAUDE.md` PLUS a role-specific file PLUS role-specific inventory files. Only useful when you're running multiple parallel terminals with assigned roles.

The role list from TurtleWolfe's workflow:

```
operator, stw-liaison, cto, architect, coordinator, security, toolsmith,
devops, product-owner, planner, wireframe-generator, preview-host,
wireframe-qa, validator, inspector, author, test-engineer, developer,
auditor, qa-lead, tech-writer, docker-captain
```

Each role maps to a file like `.claude/roles/toolsmith.md` which tells Claude what that role is responsible for and what inventory it needs loaded.

**Do not use `/prime` on Day 1.** Use `/prep`.

**Do use `/prime` in Chapter 05** when you're running the 27-terminal tmux assembly line and need each terminal to know its specific job.

Full coverage in [Chapter 05 — Advanced Orchestration](../../05-advanced-orchestration/).

---

## `/prime_repositories` — multi-repo priming

**Starter kit:** YES
**Scope:** personal (global)

A specialized variant for workflows spanning multiple related repos (e.g., a plugin + its host application). Hard-codes the paths of related READMEs, architecture docs, and key source files, and reads them all at once.

**Use case:** You're working on an integration between two repos and need both primed simultaneously. Write a custom `/prime_<project>` for each such workflow.

**Day 1: skip.**

---

## The rule of priming

> **Every session starts with `/prep`.**
> **Every context refill uses `/clear` + `/prep`.**
> **`/compact` is the last resort, not the first.**

Follow this and your context never gets polluted.

---

## Related

- [`02-give-it-context/priming-patterns.md`](../../02-give-it-context/priming-patterns.md) — the longer explanation with the war story
- [`../starter-kit/.claude/commands/prep.md`](../starter-kit/.claude/commands/prep.md) — the command file itself
- [`principles/context-hygiene.md`](../../principles/context-hygiene.md) — the underlying principle
