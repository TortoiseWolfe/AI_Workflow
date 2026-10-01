# Chapter 05 — Advanced Orchestration

> **Level 3 — Optional.** Read this AFTER you're comfortable with Chapters 00-04. Most TSD interns won't need this for months. Some never will. It's the signature move, not the daily move.

**Day-1 question:** *"Can I run 27 terminals in parallel?"*
**Time budget:** 2+ hours to read, days to fully internalize
**You'll finish with:** A mental model of TurtleWolfe's 27-terminal tmux assembly line and the discipline to know when to use it.

---

## What this chapter is

The 27-terminal tmux assembly line is TurtleWolfe's full-throttle orchestration setup. It's used in production on `ScriptHammer` and `TurtleWolfe` (the personal portfolio), and it's overkill for everything else. The mental model: **treat your AI workforce like a real workforce** — with roles, responsibilities, an org chart, a queue of work, and a council that votes on architectural decisions.

It looks like this:

```
┌─────────────────────────────────────────────────────────────┐
│  OPERATOR TERMINAL (outside tmux)                           │
│  - Launches the session                                     │
│  - Dispatches work to roles                                 │
│  - Monitors progress                                        │
│  - Escalates blockers to the human                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ tmux send-keys + Enter
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  TMUX SESSION "scripthammer" (27 windows)                   │
│                                                             │
│  Strategy:    CTO  ProductOwner  BusinessAnalyst            │
│  Design:      Architect  UXDesigner  UIDesigner             │
│  Wireframes:  Planner  Generator1/2/3  PreviewHost          │
│               WireframeQA  Validator  Inspector             │
│  Code:        Developer  Toolsmith  Security                │
│  Test:        TestEngineer  QALead  Auditor                 │
│  Docs:        Author  TechWriter                            │
│  Release:     DevOps  DockerCaptain  ReleaseManager         │
│               Coordinator                                   │
└─────────────────────────────────────────────────────────────┘
```

Each window is its own Claude Code session. Each session has its own role, its own context, its own primer (`/prime [role]`), and its own queue of work. They communicate by reading and writing shared files: `.terminal-status.json`, `docs/interoffice/audits/`, `docs/interoffice/rfcs/`.

---

## Why it exists

The honest answer: **most projects don't need this.** Use the SpecKit loop from Chapter 04 and you'll ship 95% of features faster than you would with the full assembly line.

The 5% where the assembly line wins:

1. **Parallel work that can't share state.** 4 wireframes that need to be generated simultaneously, but each one is its own SVG with its own validator pass.
2. **Council decisions.** A change touches security, infrastructure, and architecture. You want each council member (Security, DevOps, Architect) to weigh in independently before implementation.
3. **Long-running audits.** A security audit, a dependency audit, a compliance audit, all running at the same time on different parts of the codebase.
4. **Parallel TDD across modules.** 6 modules each needing tests + implementation, none touching the same files.

For these, the assembly line is genuinely faster because it's running 27 Claudes in parallel instead of one Claude doing everything in sequence.

---

## What's in this chapter

- [**ai-kitchen-map.html**](ai-kitchen-map.html) ([PDF](ai-kitchen-map.pdf) · just the graph: [PNG](ai-kitchen-graph.png), [SVG](ai-kitchen-graph.svg)) — the current version of this chapter as one picture: an Opus "head chef", cheap Haiku/Sonnet workers in git worktrees behind tests and a blind Opus review, plus the side agents (2026-09-30)
- [**setup-tutorial.html**](setup-tutorial.html) — build it yourself: tiered helper agents, the director workflow behind deterministic checks and a blind Opus review, the Jev shadow check, notes with a second assistant over Gmail drafts, and the gotchas that cost a day (2026-09-30)
- [**action-figure-automata.html**](action-figure-automata.html) — meet the team: the AI agents and machines behind all of this, nicknamed "the fleet", who runs where, and how the members voted on their own name (2026-10-01)
- [**the-assembly-line.md**](the-assembly-line.md) — the 7-stage pipeline diagram and how work flows through it
- [**roles.md**](roles.md) — every one of the 27 roles documented: what they do, what they read, what they write
- [**the-operator.md**](the-operator.md) — the meta-orchestrator that runs OUTSIDE tmux and dispatches to workers INSIDE — including the `tmux send-keys ... Enter` lesson that took TurtleWolfe a week to learn
- [**dispatch-and-queue.md**](dispatch-and-queue.md) — the orchestration primitives: `/dispatch`, `/queue`, `/queue-check`, `/status`
- [**rfcs-and-council.md**](rfcs-and-council.md) — governance: `/rfc`, `/rfc-vote`, `/council`, `/memo`, `/broadcast`
- [**wireframe-pipeline.md**](wireframe-pipeline.md) — the end-to-end SVG generation workflow: 11 commands, the validator script, the viewer container
- [**when-this-helps.md**](when-this-helps.md) — honest assessment of when this is worth the setup cost vs when it isn't

---

## Prerequisites for actually running this

- **tmux** installed and you know the basics (`Ctrl+b d` to detach, `tmux attach`, etc.)
- **A real project** with `.claude/roles/`, `docs/interoffice/`, and the supporting scripts (see ScriptHammer and TurtleWolfe for reference implementations)
- **Comfort with Chapter 04.** If the SpecKit loop still feels foreign, this will overwhelm you.
- **Patience.** The first week of running the assembly line is learning the lifecycle commands and watching things break.
- **The full 65-command kit installed.** Run `bash ~/repos/AI_Workflow/03-slash-commands/install-full-kit.sh` first.

---

## What this chapter is NOT

- **A tutorial you can follow on Day 1.** It's not. Don't try.
- **The right answer for every project.** It's not. Most projects should use Chapter 04.
- **A polished product.** It's TurtleWolfe's personal workflow. The scripts assume his directory structure, his role names, his conventions. Adapt or steal as needed.

---

## How to read this chapter

1. **Read [when-this-helps.md](when-this-helps.md) first.** Decide if this is worth your time before reading the rest.
2. **Read [the-assembly-line.md](the-assembly-line.md)** to get the architectural picture.
3. **Skim [roles.md](roles.md)** to see who's in the org chart.
4. **Read [the-operator.md](the-operator.md)** if you're going to actually run it — that's the meta-terminal that drives everything.
5. **Read [dispatch-and-queue.md](dispatch-and-queue.md)** and [**rfcs-and-council.md**](rfcs-and-council.md) for the protocols.
6. **Read [wireframe-pipeline.md](wireframe-pipeline.md)** if you have a use case for parallel SVG wireframe generation. Skip otherwise.

---

**Back to:** [Chapter 04 — The SpecKit Loop](../04-the-speckit-loop/) | **Up:** [Curriculum overview](../README.md)
