# Chapter 01 — Bootstrap a Repo

**Day-1 question:** *"How do I start a new project with Claude Code?"*
**Time budget:** 15 minutes
**You'll finish with:** A new repo cloned from `hello-world-ai`, renamed, booted under Docker, and a first commit shipped via `/commit`.

---

## Day-1 minimum: clone the starter

**The fastest path to a working project is to clone [`hello-world-ai`](../../hello-world-ai/) and rename it.** It's a minimal Next.js 15 + Docker Compose starter with the 10-command starter kit pre-installed at `.claude/commands/`. From clone to first commit: under 15 minutes.

Follow: [**clone-the-starter.md**](clone-the-starter.md)

Then do the [exercise](exercise.md).

That's Chapter 01. You're done. Come back for the dig-deeper if you need to bootstrap a repo without the starter.

---

## Dig deeper

### When to clone vs when to bootstrap from scratch

| Situation | Path |
|---|---|
| New side project, learning exercise, prototype | **Clone the starter.** [clone-the-starter.md](clone-the-starter.md) |
| Contributing to an existing repo | Clone the existing repo; this chapter doesn't apply |
| Your stack is not Next.js + Docker (Python, Go, Rust, etc.) | [**from-scratch.md**](from-scratch.md) — the manual bootstrap recipe |
| You want to understand what `hello-world-ai` is made of | [from-scratch.md](from-scratch.md) — it documents each template file |

### The templates directory

[`templates/`](templates/) contains the raw building blocks of `hello-world-ai`:

- [`CLAUDE.md.template`](templates/CLAUDE.md.template) — the skeleton every repo should have (explained in Chapter 02)
- [`gitignore.template`](templates/gitignore.template) — the minimum `.gitignore` for a Node + Docker project
- [`docker-compose.yml.template`](templates/docker-compose.yml.template) — Docker-first starter for any Node project
- [`env.example.template`](templates/env.example.template) — the `${VAR:-placeholder}` pattern for secrets

Use these when cloning `hello-world-ai` doesn't fit your stack.

---

## Exercise

[**exercise.md**](exercise.md) — Clone `hello-world-ai`, rename it to `my-first-ai-project`, boot it with `docker compose up`, and ship the first commit via `/commit`. 15 minutes.

---

**Previous:** [Chapter 00 — Start Here](../00-start-here/) · **Next:** [Chapter 02 — Give It Context](../02-give-it-context/) · **All parts:** [the series in order](../series.html#course)
