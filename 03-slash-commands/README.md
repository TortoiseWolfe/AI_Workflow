# Chapter 03 — Slash Commands

**Day-1 question:** *"How do I stop typing the same prompt 20 times?"*
**Time budget:** 30 minutes
**You'll finish with:** The 30-command starter kit installed in a project of yours, and one custom command you wrote yourself.

---

## Day-1 minimum: the starter kit

Slash commands are **prompt templates stored as files**. When you type `/commit`, Claude reads `.claude/commands/commit.md` and follows the instructions in that file. That's the whole mechanism.

The starter kit ships **30 commands across 7 families** — every command TurtleWolfe uses on a daily basis. The ones excluded from the starter kit (orchestration, governance, wireframe pipeline, knowledge curation) need additional infrastructure to be useful, so they live in [Chapter 05](../05-advanced-orchestration/) and the [full reference](full-reference/).

### The 30 starter-kit commands

| Family | Commands | Family doc |
|---|---|---|
| **Priming** | `prep`, `prime`, `prime_repositories` | [catalog/priming.md](catalog/priming.md) |
| **SpecKit** | `speckit.specify`, `speckit.clarify`, `speckit.plan`, `speckit.tasks`, `speckit.implement`, `speckit.analyze`, `speckit.checklist`, `speckit.constitution`, `speckit.taskstoissues`, `speckit.workflow` | [catalog/speckit.md](catalog/speckit.md) |
| **Git** | `commit`, `ship` | [catalog/git.md](catalog/git.md) |
| **Quality** | `code-review`, `security-audit`, `secrets-scan`, `audit` | [catalog/quality.md](catalog/quality.md) |
| **Testing** | `test`, `test-a11y`, `test-components`, `test-fail`, `test-hooks` | [catalog/testing.md](catalog/testing.md) |
| **Session** | `session-stats`, `session-summary`, `status`, `clean-start` | [catalog/session.md](catalog/session.md) |
| **Reading** | `read-spec`, `read-issues` | [catalog/session.md](catalog/session.md) |

> **9 of the 10 SpecKit commands** (`speckit.specify` through `speckit.taskstoissues`) are byte-identical copies of the 9 official commands shipped by [`github/spec-kit`](https://github.com/github/spec-kit) at v0.5.0+ (verified active, latest release 2026-04-02). The 10th (`speckit.workflow`) is a TurtleWolfe-authored orchestrator that runs the full SpecKit chain end-to-end with one command.
>
> **The 5 quality/testing/git/session/reading families are 100% TurtleWolfe-authored** — wrappers around lint, type-check, conventional commits, Docker exec, and the SpecKit workflow. They depend on the project being Docker-first.

All 30 are ready to copy from [`starter-kit/.claude/commands/`](starter-kit/.claude/commands/). Drop them in your project's `.claude/commands/` directory and they work immediately.

**Start here:** [exercise.md](exercise.md) — install all 30 in your project, then write your first custom command.

### Prerequisites for the SpecKit family

The 10 SpecKit commands assume `github/spec-kit` is initialized in your project (`.specify/` directory present). If it's not, the commands will tell you to run `specify init` first. Two install paths:

```bash
# Persistent install (recommended) — replace v0.5.0 with the current latest
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v0.5.0
specify init                       # initialize in current project

# Or one-time usage
uvx --from git+https://github.com/github/spec-kit.git@v0.5.0 specify init
```

(Latest version verified 2026-04-06: v0.5.0, published 2026-04-02. Check [SpecKit releases](https://github.com/github/spec-kit/releases) for the current tag.)

> **For interns:** the [`hello-world-ai`](../../hello-world-ai/) starter ships with `.specify/` already initialized so Day 1 works without an extra install step. For your own projects, run `specify init` once after `git init`.

---

## Dig deeper

### Command catalog

The [`catalog/`](catalog/) directory has one doc per command family:

- [**priming.md**](catalog/priming.md) — `/prep`, `/prime [role]`, `/prime_repositories`
- [**speckit.md**](catalog/speckit.md) — the full SpecKit feature loop and the 10 commands that drive it
- [**quality.md**](catalog/quality.md) — `/code-review`, `/security-audit`, `/secrets-scan`, `/audit`
- [**testing.md**](catalog/testing.md) — `/test` and the 4 narrower test commands
- [**git.md**](catalog/git.md) — `/commit`, `/ship`
- [**session.md**](catalog/session.md) — `/session-stats`, `/session-summary`, `/status`, `/clean-start`, `/read-spec`, `/read-issues`

### Beyond the starter kit

The starter kit is 30 commands. TurtleWolfe's full live setup is **65 commands**. The other 35 fall into four families that need additional infrastructure to be useful:

| Family | Commands | Why not in starter kit | Where to learn |
|---|---|---|---|
| **Orchestration** | `dispatch`, `queue`, `queue-check`, `review-queue`, `next`, `log`, `refresh-inventories` | Need the 27-terminal tmux assembly line | [Chapter 05](../05-advanced-orchestration/) |
| **Governance/RFCs** | `rfc`, `rfc-vote`, `vote-now`, `council`, `broadcast`, `memo` | Need a council of role-based terminals | [Chapter 05](../05-advanced-orchestration/) |
| **Wireframe pipeline** | `wireframe`, `wireframe-plan`, `wireframe-prep`, `wireframe-focused`, `wireframe-fix`, `wireframe-review`, `wireframe-inspect`, `wireframe-screenshots`, `wireframe-status`, `hot-reload-viewer`, `viewer-status` | Need a `validate-wireframe.py` script and a viewer container | [Chapter 05](../05-advanced-orchestration/) |
| **Knowledge curation** | `clean-transcript`, `extract-linkedin`, `rpg_subsystem_scaffold` | TranScripts-style helpers — see [Chapter 02](../02-give-it-context/knowledge-bases.md) | [02 / knowledge-bases.md](../02-give-it-context/knowledge-bases.md) |

When you're ready, the [exercise](exercise.md) ends with a one-line install for the full set:

```bash
bash ~/repos/TSD_AI_Workflow/03-slash-commands/install-full-kit.sh
```

That copies the remaining 35 commands from `~/repos/Claude_Commandz/global/.claude/commands/` into your global `~/.claude/commands/`. (You only need to do this once globally — it's not per-project.)

### Anatomy of a slash command

Every slash command is a markdown file at `.claude/commands/<name>.md` with this shape:

```markdown
---
description: One-sentence description shown in the command list
scope: personal | project
---

Prose instructions for Claude. Use markdown headers to organize sections.

## Instructions

1. Step one
2. Step two
3. Step three

## Output

What Claude should say when done.
```

- **`description`** — shown in `/help` and fuzzy search. Keep it under 80 characters.
- **`scope: personal`** — only available in projects where you've copied the file in. Most starter-kit commands are personal.
- **`scope: project`** — shipped with a specific project. SpecKit commands are usually project-scoped because they depend on `.specify/` scripts in the repo.
- **Body** — the actual prompt. Be specific. Use numbered steps. Tell Claude what output you want.

Files can be as short as 12 lines ([`starter-kit/.claude/commands/prep.md`](starter-kit/.claude/commands/prep.md)) or as long as 530 lines (`starter-kit/.claude/commands/speckit.workflow.md`). Start short.

### When to write your own vs use a built-in

- **Built-in Claude Code commands** (`/help`, `/clear`, `/model`, `/fast`) — can't override. Don't try.
- **The 30 starter-kit commands** — copy and use as-is. Modify only if you have a specific reason.
- **Your own commands** — write one when you notice yourself typing the same 5-sentence prompt three times in a week. That's the signal.

---

## Exercise

[**exercise.md**](exercise.md) — Install the 30-command starter kit in a project. Then write your own custom command that automates a repetitive prompt you've already noticed yourself repeating. 30 minutes.

---

**Next:** [Chapter 04 — The SpecKit Loop](../04-the-speckit-loop/)
