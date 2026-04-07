# Chapter 04 Exercise — Ship a Real Feature With the SpecKit Loop

**Time budget:** 60 minutes
**Success criterion:** A real feature shipped via `/commit` and `/ship` on a real branch, with `specs/NNN-feature/` containing spec.md, plan.md, tasks.md, and Claude marked every task `[X]`.

---

## What you'll build

A small but real feature in `tsd-exercise-01` (your project from Chapter 01). Pick one of these, or invent your own:

1. **Dark mode toggle** — A button that toggles light/dark theme, persists to localStorage, defaults to system preference
2. **Word counter component** — A `<WordCount text={...} />` component with tests, stories, and a11y tests
3. **Health check endpoint** — `GET /api/health` that returns `{ status: "ok", uptime: ... }`
4. **Reading time indicator** — Shows "5 min read" on a blog post page based on word count

All four are achievable in 60 minutes via the SpecKit loop. Pick the one that interests you most.

---

## The steps

### Setup (5 min)

```bash
cd ~/repos/tsd-exercise-01
docker compose up -d
claude
```

Inside Claude:
```
/prep
```

If `.specify/` doesn't exist yet, exit Claude and run:
```bash
uvx --from git+https://github.com/github/spec-kit.git@v0.5.0 specify init
claude
/prep
```

### Step 1: `/speckit.constitution` (5 min, one-time)

If you haven't run this in `tsd-exercise-01` before:

```
/speckit.constitution
```

Write 3-5 principles for this project. Examples:
- Docker-first
- TypeScript strict mode
- TDD before implementation
- No secrets in committed files
- Conventional commits

Save and continue.

### Step 2: `/speckit.specify` (10 min)

```
/speckit.specify <your feature description here>
```

Example:
```
/speckit.specify add a dark mode toggle button to the header that persists user preference and respects system color scheme by default
```

**Read the generated spec.** Do not skip. If it's wrong, ask Claude to fix it before moving on.

### Step 3: `/speckit.clarify` (5 min)

```
/speckit.clarify
```

Answer the questions Claude asks (up to 5). Each one should be quick — multiple choice or short answer. If a question seems too important to answer in 5 words, take more time and explain in a sentence.

### Step 4: `/speckit.plan` (5 min)

```
/speckit.plan
```

**Read the plan.** Specifically check:
- File layout — does it match your project's conventions?
- Tests — are there test tasks for every implementation task?
- Data model — is it minimal? (more state = more bugs)

If anything's wrong, ask Claude to revise.

### Step 5: `/speckit.tasks` (3 min)

```
/speckit.tasks
```

Skim the task list. Sanity check: do they look mechanical? Each task should be specific enough that you'd know whether it's done or not.

### Step 6: `/speckit.analyze` (2 min)

```
/speckit.analyze
```

If there are CRITICAL issues, fix them before moving on. MEDIUM/LOW you can defer.

### Step 7: `/speckit.implement` (15 min)

```
/speckit.implement
```

Watch Claude work. Don't interrupt unless it's clearly going wrong. Each task should complete in seconds — if a task takes more than 2 minutes, something's stuck.

### Step 8: `/code-review` (5 min)

```
/code-review
```

5-phase audit. Look at the summary table. Anything in the "Remaining" column is on you to address.

### Step 9: `/test` (1 min)

```
/test
```

Should be all green. If not, you have failures to fix before shipping.

### Step 10: `/commit` (1 min)

```
/commit
```

Conventional commit, lint + type-check pre-flight, Claude Code footer. Should be one fluid motion.

### Step 11: `/ship` (1 min)

```
/ship
```

Merge to main, delete the feature branch, report. **Local only — do not push.**

---

## Verification

```bash
git log --oneline -5
ls specs/
```

You should see:
- A merge commit on main with the feature subject
- A `feat:` commit with the Claude Code footer
- A `specs/NNN-<feature>/` directory with spec.md, plan.md, tasks.md (all marked `[X]`)

```bash
docker compose exec tsd-exercise-01 pnpm test
```

All tests pass.

---

## Rubric

- [ ] `specs/NNN-<feature>/` directory exists with `spec.md`, `plan.md`, `tasks.md`
- [ ] `tasks.md` has all tasks marked `[X]` (none `[ ]`, none `[!]`)
- [ ] At least one new component or module exists in `src/`
- [ ] At least one test file exists for the new code
- [ ] All tests pass (`pnpm test` is green)
- [ ] `git log -2` shows the feature commit + the merge commit, both with the Claude Code footer
- [ ] The feature actually works in the running app (open http://localhost:3000 and see it)

If any box is unchecked, the exercise isn't complete. The point is to feel the entire loop end-to-end, not to ship perfect code.

---

## Common pitfalls

| Pitfall | Fix |
|---|---|
| You skipped `/speckit.clarify` and the spec was vague | Re-run `/speckit.specify` with a sharper description, then run `/speckit.clarify` |
| `/speckit.implement` keeps failing on the same task | Read the error. The plan was probably wrong. Go back to `/speckit.plan`, fix it, re-run `/speckit.tasks`, re-run `/speckit.implement`. Don't paper over bad design. |
| `/code-review` finds 20 issues you don't want to fix | The plan was too ambitious. Either accept the fixes or revisit the plan to descope. |
| `/commit` fails on lint | Read the lint error. Ask Claude to fix it. Re-run `/commit`. |
| You ran out of time | Pick a smaller feature. The loop is the lesson, not the feature. |

---

## What you learned

- The full loop is 10 commands and ~60 minutes for a real feature
- Each phase produces an artifact you can review before proceeding
- Bugs caught in `/speckit.analyze` cost minutes; bugs caught in `/code-review` cost minutes; bugs caught in production cost hours
- The spec is the source of truth — `git blame` for "what was this supposed to do"
- The discipline scales: 60 min for a small feature, days for a big one, same loop

---

**Next:** [Chapter 05 — Advanced Orchestration](../05-advanced-orchestration/) (Level 3 / Optional)
