# Chapter 02 — Give It Context

**Day-1 question:** *"Why does Claude keep missing obvious things about my project?"*
**Time budget:** 30 minutes
**You'll finish with:** A working `CLAUDE.md` for a project of your choice, and a clear mental model of the three layers of context.

---

## Day-1 minimum: the three layers

Claude Code has amnesia between sessions. Every new conversation starts with zero knowledge of your project. You give it context via **three layers**, in order of how often they change:

| Layer | Changes | Where it lives | Loaded by |
|---|---|---|---|
| **1. Knowledge** | Rarely | Outside your repo (Claude Projects, documentation sites) | The human, before starting Claude Code |
| **2. Instructions** | Per repo, updated when conventions change | `CLAUDE.md` at repo root | Claude automatically on session start |
| **3. Operations** | Per repo, updated when you add commands | `.claude/commands/*.md` | Claude when the user types `/command` |

Writing `CLAUDE.md` well is the single highest-leverage investment you can make in a repo. A 150-line `CLAUDE.md` saves you hundreds of "don't do that" interruptions later.

**Start here:** [**writing-claude-md.md**](writing-claude-md.md) — how to write a `CLAUDE.md` that actually works, with three annotated examples from real production repos.

Then do the [exercise](exercise.md).

---

## Dig deeper

### The three layers in detail

- [**writing-claude-md.md**](writing-claude-md.md) — Layer 2. Anatomy of a `CLAUDE.md` with annotated excerpts from ScriptHammer, SpokeToWork, and TurtleWolfe.
- [**priming-patterns.md**](priming-patterns.md) — How to reload context mid-session. `/prep`, `/prime [role]`, `/clear`+`/prep`, and why `/compact` is the trap.
- [**knowledge-bases.md**](knowledge-bases.md) — Layer 1. Using Claude Projects to give Claude background knowledge that doesn't belong in your repo (frameworks, best practices, expert transcripts).

### Why context matters (a 30-second story)

You write a React component. You ask Claude to add a test. Claude writes a Jest test. Your repo uses Vitest. You say "no, Vitest." Claude rewrites. It uses `describe`/`it`. Your repo uses `describe`/`test`. You say "no, `test` not `it`". Claude rewrites. Your repo scaffolds components with 5 files (index, Component, test, stories, a11y test). Claude only wrote the one test file. You say "actually you need to generate the 5-file scaffold." Claude apologizes.

Every one of those corrections is a line you could have written in `CLAUDE.md` once, and never typed again. The time you spend in Chapter 02 pays back within a week.

---

## Exercise

[**exercise.md**](exercise.md) — Write a `CLAUDE.md` for a project you already have (or the `tsd-exercise-01` you made in Chapter 01). Run `/prep`. Ask Claude a question you expect it to get wrong without context. Confirm it gets it right now. 30 minutes.

---

**Next:** [Chapter 03 — Slash Commands](../03-slash-commands/)
