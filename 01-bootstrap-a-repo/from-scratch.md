# Bootstrap From Scratch

Use this when `hello-world-ai` doesn't fit your stack — you're building in Python, Go, Rust, or any non-Next.js project. This recipe documents the **seven files every AI-assisted project should have** from day one, and where each one comes from.

Day-1 minimum path: clone `hello-world-ai` instead. [clone-the-starter.md](clone-the-starter.md). This page is the fallback.

---

## The seven files

Every repo bootstrapped this way gets these seven files on the first commit:

| # | File | Purpose | Template |
|---|---|---|---|
| 1 | `README.md` | What this repo is, how to boot it | You write this |
| 2 | `CLAUDE.md` | Rules for Claude in this repo | [templates/CLAUDE.md.template](templates/CLAUDE.md.template) |
| 3 | `.gitignore` | Keep junk out of git | [templates/gitignore.template](templates/gitignore.template) |
| 4 | `docker-compose.yml` | Docker-first dev env | [templates/docker-compose.yml.template](templates/docker-compose.yml.template) |
| 5 | `.env.example` | Secret variable names only | [templates/env.example.template](templates/env.example.template) |
| 6 | `.claude/commands/prep.md` | Silent CLAUDE.md reader | Copy from `03-slash-commands/starter-kit/.claude/commands/prep.md` |
| 7 | `.claude/commands/commit.md` | Lint + type-check + commit | Copy from `03-slash-commands/starter-kit/.claude/commands/commit.md` |

Those seven files get you to the same place `hello-world-ai` gets you: a repo where `/prep` and `/commit` work on Day 1.

## The bootstrap sequence

```bash
# 1. Create the directory
mkdir ~/repos/my-new-project
cd ~/repos/my-new-project

# 2. Initialize git
git init

# 3. Copy the templates
cp ~/repos/AI_Workflow/01-bootstrap-a-repo/templates/CLAUDE.md.template ./CLAUDE.md
cp ~/repos/AI_Workflow/01-bootstrap-a-repo/templates/gitignore.template ./.gitignore
cp ~/repos/AI_Workflow/01-bootstrap-a-repo/templates/docker-compose.yml.template ./docker-compose.yml
cp ~/repos/AI_Workflow/01-bootstrap-a-repo/templates/env.example.template ./.env.example

# 4. Copy the two Day-1 commands
mkdir -p .claude/commands
cp ~/repos/AI_Workflow/03-slash-commands/starter-kit/.claude/commands/prep.md .claude/commands/
cp ~/repos/AI_Workflow/03-slash-commands/starter-kit/.claude/commands/commit.md .claude/commands/

# 5. Fill in the placeholders in CLAUDE.md and docker-compose.yml
$EDITOR CLAUDE.md docker-compose.yml

# 6. Write a real README
$EDITOR README.md

# 7. First commit
git add -A
git commit -m "chore: bootstrap project skeleton"
```

## Filling in the placeholders

### `CLAUDE.md`

The template has `{{PROJECT_NAME}}`, `{{STACK}}`, and `{{DOCKER_SERVICE}}` placeholders. Replace them before your first commit. Chapter 02 explains the anatomy of `CLAUDE.md` in detail — skim it before writing your own.

### `docker-compose.yml`

The template is a minimal Node.js service. For other stacks:

- **Python** — change the `image` to `python:3.12-slim`, change `command` to `python -m uvicorn app:app` or similar
- **Go** — change the `image` to `golang:1.22`, change `command` to `go run .`
- **Rust** — change the `image` to `rust:1.78`, change `command` to `cargo watch -x run`

The important part isn't the stack; it's that **your dev loop runs inside the container from day one**. See [`principles/docker-first.md`](../principles/docker-first.md) for why.

### `.env.example`

List every secret name your project will use, with empty values or inert placeholders. **Never** commit real values.

```bash
# .env.example
DATABASE_URL=postgres://postgres:change-me@db:5432/dev
API_KEY=set-in-local-env-file
```

Your real `.env` file stays gitignored.

---

## After the bootstrap

1. Run `docker compose up` — confirm the dev loop boots
2. In another terminal: `claude`, then `/prep` — confirm you see only `Read project context. Ready.`
3. Make a trivial edit, then `/commit` — confirm lint/type-check run and the commit lands

If all three work, your bootstrap is complete. Move on to Chapter 02.

---

## Related

- [clone-the-starter.md](clone-the-starter.md) — the Day-1-minimum path
- [Chapter 02 — Give It Context](../02-give-it-context/) — how to write the `CLAUDE.md` you just created
- [`principles/docker-first.md`](../principles/docker-first.md) — the "why" behind `docker-compose.yml` from day one
