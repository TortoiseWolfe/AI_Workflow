# Writing CLAUDE.md

A `CLAUDE.md` file at your repo root tells Claude the rules before you ever type a prompt. Every new conversation loads it automatically. Done well, it prevents 80% of the "no, that's not how we do it here" corrections.

This page is a **reference**, not a template. The template lives at [`01-bootstrap-a-repo/templates/CLAUDE.md.template`](../01-bootstrap-a-repo/templates/CLAUDE.md.template). This page teaches you how to *write* one.

---

## The anatomy of a working CLAUDE.md

Every production `CLAUDE.md` in TurtleWolfe's workspace has the same eight sections in the same order. Some are tiny, some are long. But the skeleton is the same:

1. **Header** — one sentence saying what this file is for
2. **Core Development Principles** — 3-5 non-negotiables (one line each)
3. **Mandates** — Docker-first, secrets rules, platform rules (the rules you'd get yelled at for breaking)
4. **Essential Commands** — the 5-10 commands you'd paste into a teammate's terminal on their first day
5. **Stack** — the frameworks, versions, and package manager
6. **Project Structure** — a 10-line tree of the important directories
7. **Testing Stack** — what runner, what assertion library, what coverage rules
8. **Deployment** — one sentence about where this runs in production

That's it. If your `CLAUDE.md` is missing any of these, add them. If it has more than those (project history, team bios, a changelog), cut them — that's not context Claude needs.

## Example 1: ScriptHammer (production PWA template)

```markdown
# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Core Development Principles

1. **Proper Solutions Over Quick Fixes** - Implement correctly the first time
2. **Root Cause Analysis** - Fix underlying issues, not symptoms
3. **Stability Over Speed** - This is a production template
4. **Clean Architecture** - Follow established patterns consistently
5. **No Technical Debt** - Never commit TODOs or workarounds
```

**Note the phrasing.** These are *rules*, not aspirations. "Proper Solutions Over Quick Fixes" tells Claude to push back when you ask for a band-aid fix. Claude will say "are you sure you want to do this — the proper fix is X." That's the goal.

```markdown
## Docker-First Development (MANDATORY)

**CRITICAL**: This project REQUIRES Docker. Local pnpm/npm commands are NOT supported.

### NEVER Install Packages Locally

**ABSOLUTELY FORBIDDEN**:
npm install
pnpm install

### CORRECT
docker compose exec scripthammer pnpm install
```

**Note the specificity.** "Do not install packages" is weak. "Never run `pnpm install` on the host, only `docker compose exec scripthammer pnpm install`" is strong. **Give Claude the exact commands**, not just the prohibition. If you only prohibit, Claude tries to find the allowed alternative and often gets it wrong.

The actual file goes on for ~200 more lines covering component scaffolding, the SpecKit workflow, the test stack, and deployment. Read the real one at `~/repos/ScriptHammer/CLAUDE.md` once — treat it as a masterclass.

## Example 2: SpokeToWork (secrets-heavy project)

SpokeToWork uses Supabase and local JWTs. Its `CLAUDE.md` leads with the secrets rule because that's the single most dangerous thing Claude could get wrong:

```markdown
## NEVER Hardcode Secrets in Committed Files (MANDATORY)

**CRITICAL**: No secret, token, key, or credential may appear as a literal
value in any file that is committed to git.

### The Rules

1. **ALL secrets go in `.env`** (gitignored). No exceptions.
2. **Committed files use `${VAR:-placeholder}`** where `placeholder` is a
   non-secret default like `change-me-realtime-secret-key-base` or
   `set-anon-key-in-env-file`.
3. **`.env.example` shows variable names only** with commented-out
   placeholder values.
4. **NEVER allowlist secrets in `.gitleaks.toml`** — not in `regexes`,
   not in `commits`, not anywhere.
5. **If a secret leaks into git history**, scrub it with
   `git-filter-repo --replace-text` and force push.
```

**Note the justification structure.** Each rule has a "why" embedded. Rule 4 doesn't just say "never allowlist secrets" — it says "not in regexes, not in commits, not anywhere" because some Claude session in the past tried to work around a rule by finding an exception. The rule grew teeth from experience.

**Lesson:** When Claude surprises you by violating an implicit rule, write it down explicitly. Your `CLAUDE.md` grows teeth over time.

## Example 3: TurtleWolfe (portfolio with pending migration)

TurtleWolfe's `CLAUDE.md` has a section that most don't: **pending configuration TODOs**:

```markdown
## Pending Configuration (TODO)

- **basePath Restoration**: Once the Squarespace domain redirect to GitHub
  Pages is configured, restore `/TurtleWolfe/` as the basePath in
  `public/manifest.json` (icon paths, start_url, scope, shortcuts,
  screenshots, share_target) and verify `next.config.ts` auto-detection
  picks it up.
- **Portfolio Mode**: Supabase is currently disabled. `useAuth()` returns
  a safe default context when used outside `AuthProvider`. No auth secrets
  are required for CI/CD.
```

**Why this works.** These are *facts Claude should know* that aren't derivable from reading the code. The basePath situation is a deliberate temporary state. Without this section, Claude would see `basePath: ''` in `next.config.ts`, assume it was a bug, and "fix" it. With this section, Claude knows to leave it alone until the migration completes.

**Lesson:** If your repo has deliberate quirks ("this looks wrong but is correct because X"), document them in `CLAUDE.md`. Code alone can't express intent.

---

## What NOT to put in CLAUDE.md

- **Architecture lectures.** Claude can read your code. It doesn't need a 2-page explanation of your MVC pattern — a 5-line project tree will do.
- **Team bios.** "Our team values TDD" is a rule, not a bio. Put it in principles. Skip names and roles.
- **Onboarding boilerplate.** "Welcome to the project!" — Claude doesn't have feelings. Cut the fluff.
- **Changelog.** That's what `git log` is for.
- **Links to documentation you haven't read.** If you wouldn't expect Claude to fetch a URL and internalize it, don't link it.
- **Duplication of README.md.** `README.md` is for humans. `CLAUDE.md` is for Claude. They should share facts (tech stack) but serve different purposes (README = how to use, CLAUDE = how to modify).

## How long should CLAUDE.md be?

Target: **100-250 lines**. If it's under 50, you're under-specifying. If it's over 300, you're probably repeating yourself — split into multiple files and reference them. ScriptHammer's is ~450 lines and it's at the upper limit of what's manageable. Most should be smaller.

Claude loads the whole file every session. Every line you add is a line loaded on every conversation. Be ruthless.

## The "adding teeth" pattern

Don't try to write the perfect `CLAUDE.md` on Day 1. Write a 50-line starter. Then:

1. **Work with Claude.** Ship some commits.
2. **Watch for corrections you make twice.** "Don't use `it`, use `test`." "Run lint inside the container."
3. **Every repeat correction becomes a line in `CLAUDE.md`.**
4. **Every month or two, re-read CLAUDE.md** and delete anything that no longer applies.

In six weeks you'll have a 200-line `CLAUDE.md` that catches every common mistake before it happens. That's the goal.

---

## Related

- [priming-patterns.md](priming-patterns.md) — how to reload your `CLAUDE.md` mid-session
- [knowledge-bases.md](knowledge-bases.md) — for context that shouldn't live in the repo
- [`01-bootstrap-a-repo/templates/CLAUDE.md.template`](../01-bootstrap-a-repo/templates/CLAUDE.md.template) — the starter template
- [`principles/context-hygiene.md`](../principles/context-hygiene.md) — the war story behind `/clear` over `/compact`
