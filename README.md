# TSD AI Workflow

**A teaching curriculum for interns at The Software Dojo.** Learn to work with Claude Code the way TurtleWolfe works with Claude Code — Docker-first, spec-first, and terminal-orchestrated.

This repo does not teach you Claude Code itself. It teaches you a **workflow** for building real software with an AI pair programmer, using conventions that have survived 20+ production repos.

## Who this is for

- New interns at TSD who have Claude Code installed but don't know what to do with it on Day 1
- Developers who've used Claude Code for scripts and want to adopt it for real feature work
- Mentors who want a single link to hand new hires instead of repeating the same onboarding conversation

## The three Day-1 questions

Every intern shows up with the same three questions. This repo answers them in order:

1. **How do I start a new repo with AI?** → [Chapter 01](01-bootstrap-a-repo/)
2. **How do I give Claude context so it's actually useful?** → [Chapter 02](02-give-it-context/)
3. **What slash commands do I use, and when?** → [Chapter 03](03-slash-commands/)

Everything else is advanced material you grow into.

## How to read this repo

Each chapter follows the same shape:

1. **Day-1 minimum** — the first two pages. Read this, do the exercise, you're productive.
2. **Dig deeper** — the rest of the chapter. Come back to it when you have questions.
3. **Exercise** — a 15-minute hands-on task. Success = a real artifact sitting in your repo.

Chapters are independent. You can read 03 before 02 if you're in a hurry. But the exercises build on each other.

## Chapter map

| # | Chapter | Day-1 question | Time |
|---|---|---|---|
| 00 | [Start Here](00-start-here/) | "Is my setup even working?" | 15 min |
| 01 | [Bootstrap a Repo](01-bootstrap-a-repo/) | "How do I start a new project?" | 15 min |
| 02 | [Give It Context](02-give-it-context/) | "Why does Claude keep missing obvious things?" | 30 min |
| 03 | [Slash Commands](03-slash-commands/) | "How do I stop typing the same prompt 20 times?" | 30 min |
| 04 | [The SpecKit Loop](04-the-speckit-loop/) | "How do I ship a whole feature without getting lost?" | 60 min |
| 05 | [Advanced Orchestration](05-advanced-orchestration/) | "Can I run 27 terminals in parallel?" (Level 3 / Optional) | 2+ hours |

Plus [`principles/`](principles/) — the *why* behind every rule, one file per principle, one war story each.

## Pictures of the workflow

- [**The AI Kitchen map**](05-advanced-orchestration/ai-kitchen-map.html) ([PDF](05-advanced-orchestration/ai-kitchen-map.pdf)): the whole current setup on one page. An Opus "head chef" hands work to cheap Haiku/Sonnet cooks in separate git worktrees, tests decide pass or fail, and a blind Opus review tastes before anything ships.
- [**Head chef, line cooks**](05-advanced-orchestration/head-chef-line-cooks.html): why it's built this way. What the "let cheap agents do the grunt work" advice gets right, why local models don't fit an 8 GB card, and how the first real run went.
- [**Build your AI kitchen**](05-advanced-orchestration/setup-tutorial.html): the setup tutorial. How to wire up the tiered helpers, the director workflow, the cheap Jev yes/no check, notes with a second assistant, and the gotchas that cost us a day.

## The companion starter repo

Chapter 01's exercise has you clone [`hello-world-ai`](https://github.com/TurtleWolfe/hello-world-ai) (a companion repo) as a starting point instead of bootstrapping from zero. It's a minimal Next.js + Docker setup with the 10-command starter kit already installed at `.claude/commands/`. First commit: under 15 minutes from `git clone` to `docker compose up` to a shipped change.

> **Note:** `hello-world-ai` lives at `~/repos/hello-world-ai` on the machine that produced this curriculum. Ask your mentor for the current clone URL.

## What this repo is NOT

- **Not a Claude Code tutorial.** It assumes you've run `/help` at least once. If you haven't, read [Anthropic's docs](https://docs.claude.com/claude-code) first.
- **Not a generic SpecKit guide.** SpecKit has its own docs. This repo teaches how the TSD workflow *uses* SpecKit inside a larger loop.
- **Not a replica of [`Claude_Commandz`](https://github.com/TurtleWolfe/Claude_Commandz).** That repo is TurtleWolfe's full 65-command disaster-recovery backup. The [Chapter 03 starter kit](03-slash-commands/starter-kit/) here is the minimal 10 commands an intern actually uses in week one.
- **Not a code library.** No generators, no scaffolds. This is documentation plus exercises.

## Prerequisites

- [Claude Code](https://docs.claude.com/claude-code) installed and working (`claude --version` returns something)
- [Docker Desktop](https://docs.docker.com/get-docker/) installed (required — Chapter 01 fails without it)
- [Git](https://git-scm.com/) installed
- A terminal you're comfortable in
- Optional but helpful: a GitHub account

## Feedback

If you hit a question the repo didn't answer, or an exercise that didn't work, **open an issue**. The `/principles` directory exists precisely because every rule in here started as a war story. Your question is the next war story.

---

**Ready?** Start with [Chapter 00](00-start-here/).
