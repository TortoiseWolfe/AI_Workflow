# Walkthrough — Cookie Consent Modal

A complete end-to-end example. Start with a one-line feature description, finish with a merged PR. This is what the loop looks like in real life.

**Project:** `tsd-exercise-01` (from Chapter 01 — Next.js 15 + Docker Compose)
**Feature:** A cookie consent modal that blocks analytics until the user accepts.
**Branch:** auto-created by `/speckit.specify`
**Total time:** ~50 minutes (real time, including thinking)

---

## Pre-flight

```bash
cd ~/repos/tsd-exercise-01
docker compose up -d
claude
```

In Claude:
```
/prep
```

Output: `Read project context. Ready.`

(One step. Every session.)

## Step 1 — `/speckit.constitution` (one-time)

You only run this once per project. If you've already run it, skip to step 2.

```
/speckit.constitution
```

Claude reads `.specify/memory/constitution.md` (if it exists) or creates one. It walks you through naming the project's non-negotiable principles. For `tsd-exercise-01` you might write:

```markdown
# Project Constitution

## Principles

1. **Docker-first** — All commands run inside the container. Never `npm install` on the host.
2. **TypeScript strict mode** — No `any`. No `@ts-ignore` without an issue link.
3. **TDD** — Tests written before implementation. New code without tests is rejected in /code-review.
4. **No secrets in committed files** — `${VAR:-placeholder}` pattern for env vars.
5. **Atomic commits** — Each commit ships one logical change.
```

Claude writes this to `.specify/memory/constitution.md` and reports the version (`v1.0.0`).

**Why this matters:** every later command (`/speckit.plan`, `/speckit.analyze`) reads this file and enforces the principles. You set the rules once; the rest of the loop respects them.

## Step 2 — `/speckit.specify`

```
/speckit.specify add a cookie consent modal that blocks analytics scripts until the user accepts
```

Claude:
1. Generates a short name: `cookie-consent`
2. Scans existing branches and specs for naming collisions, picks the next number (e.g., `005`)
3. Creates branch `005-cookie-consent`
4. Creates `specs/005-cookie-consent/spec.md` from the SpecKit template
5. Fills the spec with informed guesses, leaving up to 3 `[NEEDS CLARIFICATION]` markers for ambiguous decisions
6. Generates `specs/005-cookie-consent/checklists/requirements.md`
7. Validates the spec against the checklist, iterates up to 3 times
8. Reports the result

**Output you should see:**

```
Branch created: 005-cookie-consent
Spec written:   specs/005-cookie-consent/spec.md
Checklist:      specs/005-cookie-consent/checklists/requirements.md

Spec validation: 14/16 items pass

Open clarifications:
  Q1: Should consent be remembered across browsers (server-side) or per-browser (localStorage)?
  Q2: How long is consent valid before re-asking?
  Q3: When the user rejects, do we block ALL analytics or only non-essential?

Run /speckit.clarify to resolve, or /speckit.plan to proceed with defaults.
```

**Open the spec file** and read it. It's now under version control on the new branch. Don't skim — actually read it. If something is wrong, ask Claude to fix it before moving on.

## Step 3 — `/speckit.clarify`

```
/speckit.clarify
```

Claude presents the questions one at a time, in priority order. Each question is multiple-choice or short-answer:

```
Q1: Should consent be remembered across browsers (server-side) or per-browser (localStorage)?

| Option | Answer                                              | Implications                                       |
|--------|-----------------------------------------------------|----------------------------------------------------|
| A      | Per-browser (localStorage)                          | Simpler, no backend, user reconsents each browser  |
| B      | Server-side, keyed by session cookie                | Requires auth, consent persists across browsers    |
| C      | Server-side, keyed by IP                            | No auth needed but unreliable for mobile/dynamic IPs|
| Custom | Provide your own answer                             |                                                    |

Your choice:
```

You answer `A`. Claude updates the spec — adds a Functional Requirement saying "consent stored in localStorage", removes the question from Open Questions, and saves the file.

Then question 2, then question 3. After all 3, Claude reports:

```
Clarifications complete.
Spec:            specs/005-cookie-consent/spec.md
Sessions added:  ## Clarifications → ### Session 2026-04-06
Questions asked: 3 / 5
Open questions remaining: 0

Next: /speckit.plan
```

## Step 4 — `/speckit.plan`

```
/speckit.plan
```

Claude reads the now-clarified spec, the constitution, and `CLAUDE.md`. Then generates:

- `specs/005-cookie-consent/plan.md` — stack choices, file layout, architecture
- `specs/005-cookie-consent/research.md` — technical decisions
- `specs/005-cookie-consent/data-model.md` — `ConsentPreference` entity
- `specs/005-cookie-consent/contracts/` — interface signatures
- `specs/005-cookie-consent/quickstart.md` — integration scenario

**Open `plan.md`.** You'll see something like:

```markdown
## Stack & Constraints
- Framework: Next.js 15 (from CLAUDE.md)
- Storage: localStorage (from spec clarification 1)
- Component pattern: 5-file atomic (from CLAUDE.md)
- Tests: Vitest (from CLAUDE.md)

## File Layout
src/components/ConsentModal/
├── index.tsx
├── ConsentModal.tsx
├── ConsentModal.test.tsx
├── ConsentModal.stories.tsx
└── ConsentModal.accessibility.test.tsx
src/lib/consent.ts
src/lib/consent.test.ts
src/app/layout.tsx (modified)

## Data Model
ConsentPreference: { acceptedAt: ISO8601, version: 1 }

## Contracts
getConsent(): ConsentPreference | null
setConsent(): void
<ConsentModal />: self-mounting component, props: none
```

The plan is the **last stop before tasks**. Read it. If the architecture is wrong, fix it now — fixing in plan is cheap, fixing in code is expensive.

## Step 5 — `/speckit.tasks`

```
/speckit.tasks
```

Claude reads the plan and produces `specs/005-cookie-consent/tasks.md`:

```markdown
## Phase 1: Setup
- [ ] T001 — Create empty `src/components/ConsentModal/` directory

## Phase 2: Tests (TDD)
- [ ] T010 [P] — Write `src/lib/consent.test.ts` (round-trip get/set)
- [ ] T011 [P] — Write `src/components/ConsentModal/ConsentModal.test.tsx`
- [ ] T012 [P] — Write `src/components/ConsentModal/ConsentModal.accessibility.test.tsx`

## Phase 3: Core
- [ ] T020 — Implement `src/lib/consent.ts` (depends on T010)
- [ ] T021 — Implement `src/components/ConsentModal/ConsentModal.tsx` (depends on T011, T012)
- [ ] T022 — Implement `src/components/ConsentModal/index.tsx` (barrel export)

## Phase 4: Integration
- [ ] T030 — Mount `<ConsentModal />` in `src/app/layout.tsx`
- [ ] T031 — Wire analytics gating (conditional render of `<Script />`)

## Phase 5: Polish
- [ ] T040 [P] — Add `ConsentModal.stories.tsx` for Storybook
- [ ] T041 [P] — Add changelog entry
```

11 tasks, 5 phases, parallelism marked. Each task is mechanical to execute.

## Step 6 — `/speckit.analyze` (optional, recommended)

```
/speckit.analyze
```

Read-only check across spec, plan, tasks, and constitution. Output:

```
### Specification Analysis Report

| ID  | Category    | Severity | Location              | Summary                                          | Recommendation                                |
|-----|-------------|----------|-----------------------|--------------------------------------------------|-----------------------------------------------|
| C1  | Coverage    | MEDIUM   | tasks.md              | T031 (analytics gating) has no test task         | Add T013: integration test for gated analytics|
| A1  | Ambiguity   | LOW      | spec.md FR-003        | "Modal is accessible" — unmeasurable             | Specify WCAG 2.1 AA + keyboard-only flow      |

Coverage: 10/11 requirements have tasks (91%)
Critical issues: 0
```

You ask Claude to fix C1 (add the missing test task) and A1 (sharpen the FR). Claude updates `tasks.md` and `spec.md`. Re-run `/speckit.analyze`:

```
Coverage: 11/11 requirements have tasks (100%)
Critical issues: 0
LOW issues: 0

Next: /speckit.implement
```

Green. Proceed.

## Step 7 — `/speckit.implement`

```
/speckit.implement
```

Claude executes the tasks, phase by phase:

```
═══════════════════════════════════════════
Phase 1: Setup
═══════════════════════════════════════════
✓ T001 — Created src/components/ConsentModal/ (0.2s)

═══════════════════════════════════════════
Phase 2: Tests (TDD)
═══════════════════════════════════════════
✓ T010 — Wrote src/lib/consent.test.ts (3 tests, all failing as expected) (1.4s)
✓ T011 — Wrote ConsentModal.test.tsx (5 tests, failing as expected) (2.1s)
✓ T012 — Wrote ConsentModal.accessibility.test.tsx (3 tests, failing as expected) (1.8s)
✓ T013 — Wrote analytics-gating integration test (failing as expected) (1.7s)

Phase boundary: tests are red ✓ (correct for TDD)

═══════════════════════════════════════════
Phase 3: Core
═══════════════════════════════════════════
✓ T020 — Implemented src/lib/consent.ts (T010 now passing: 3/3) (3.2s)
✓ T021 — Implemented ConsentModal.tsx (T011: 5/5, T012: 3/3) (8.4s)
✓ T022 — Implemented index.tsx (0.4s)

═══════════════════════════════════════════
Phase 4: Integration
═══════════════════════════════════════════
✓ T030 — Mounted <ConsentModal /> in layout.tsx (1.1s)
✓ T031 — Wired analytics gating (T013 now passing) (2.3s)

═══════════════════════════════════════════
Phase 5: Polish
═══════════════════════════════════════════
✓ T040 — Added ConsentModal.stories.tsx (1.5s)
✓ T041 — Added changelog entry (0.3s)

═══════════════════════════════════════════
BUILD COMPLETE
═══════════════════════════════════════════
Tasks: 12/12 ✓
Test suite: PASS (47 tests, 1.2s)
Lint: PASS
Type-check: PASS

Next: /code-review
```

12 tasks, all green. You watched the whole thing. You can interrupt with `Esc` at any point if Claude goes sideways.

## Step 8 — `/code-review`

```
/code-review
```

Five-phase audit. Output:

```
| Category       | Found | Fixed | Remaining |
|----------------|-------|-------|-----------|
| Security       |     1 |     1 |         0 |
| Performance    |     0 |     0 |         0 |
| Code Quality   |     2 |     2 |         0 |
| Test Coverage  |     0 |     0 |         0 |
```

Security finding: the consent value didn't have a version field check on read — fixed. Code quality: an unused import in `index.tsx` and a missing `aria-label` on the close button — fixed.

All zeros remaining. Ship it.

## Step 9 — `/test`

```
/test
```

```
Test Results
Passing: 47
Failing:  0
Skipped:  0
Duration: 1.3s
```

Green. Proceed.

## Step 10 — `/commit`

```
/commit
```

Claude runs lint and type-check (Docker), they pass, then commits:

```
feat(consent): add cookie consent modal blocking analytics

Closes spec 005-cookie-consent. Modal blocks analytics scripts until
user accepts. Consent stored in localStorage with version field.
WCAG 2.1 AA compliant with keyboard navigation and focus trap.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

Hash: `a1b2c3d`. Branch: `005-cookie-consent`.

## Step 11 — `/ship`

```
/ship
```

Pre-flight, switch to main, merge with `--no-ff`, delete the feature branch, list stray branches.

```
═══════════════════════════════════════════
SHIP COMPLETE
═══════════════════════════════════════════
Merged:   005-cookie-consent → main (--no-ff)
Hash:     a1b2c3d → e4f5g6h (merge commit)
Branch:   005-cookie-consent (deleted)
Stray:    none

Local only — `git push` when ready.
═══════════════════════════════════════════
```

You decide when to push.

---

## What just happened

You went from a one-line description to a merged feature with:

- Spec, plan, data model, contracts, tasks (5 markdown files of design)
- 4 test files (unit, component, accessibility, integration), 16 tests
- 5-file atomic component
- localStorage helper with version handling
- Layout integration with conditional analytics
- Storybook story
- Changelog entry
- Conventional commit with Claude Code attribution
- Merged to main, branch cleaned up

In ~50 minutes. **Without losing track of what you were building once.**

Read back the artifacts in `specs/005-cookie-consent/`:
- `spec.md` — what you wanted, plus the clarifications
- `plan.md` — how it was going to be built
- `tasks.md` — every task checked off
- `data-model.md`, `contracts/`, `research.md`, `quickstart.md` — supporting docs

When you come back to this feature in 6 months to add per-vendor toggles, you read these files first. They're the source of truth for "what does this code do and why."

---

## Common detours

| Situation | What to do |
|---|---|
| `/speckit.clarify` asks a question you don't know the answer to | Pick the most reasonable option and add a TODO. Don't block on perfection. |
| `/speckit.plan` proposes an architecture you disagree with | Tell Claude: "Replan with X instead of Y". Don't accept a plan you wouldn't write yourself. |
| `/speckit.analyze` finds a CRITICAL issue | Stop. Fix it before `/speckit.implement`. Re-run `/speckit.analyze`. |
| `/speckit.implement` gets a test failure mid-phase | Claude halts. Ask Claude to fix the failure. Re-run `/speckit.implement` — it picks up from the failed task. |
| `/code-review` finds something you don't want fixed | Tell Claude to skip that finding and explain why. |
| `/test` fails after `/speckit.implement` | Bug in the implementation. Claude tracks it down. The tests already exist, so the failure is precise. |

---

## Related

- [README.md](README.md) — the loop diagram and when to use it
- [when-to-use-what.md](when-to-use-what.md) — decision tree for loop vs no-loop
- [`../03-slash-commands/catalog/speckit.md`](../03-slash-commands/catalog/speckit.md) — full reference for each command
- [`../principles/spec-before-code.md`](../principles/spec-before-code.md) — why this discipline exists
- [exercise.md](exercise.md) — your turn
