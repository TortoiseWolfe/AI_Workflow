# Command Catalog — SpecKit

[**`github/spec-kit`**](https://github.com/github/spec-kit) is the disciplined feature-development workflow that replaces "ask Claude to just build it." It's a 7+ phase pipeline where each phase produces a markdown artifact that the next phase consumes. Used consistently, it prevents scope creep, spec drift, and half-implemented features.

> **Status (verified April 2026):** Active. v0.5.0+. 85.7k stars. Last commit and 8+ merged PRs *the same day this catalog was written*. Native Claude Code skill integration since v0.4.5+. Not deprecated, not abandoned, not replaced. Don't believe rumors — check the [repo](https://github.com/github/spec-kit) yourself.

Chapter 04 walks through the full loop end-to-end. This page is the reference for each individual command.

---

## Installing SpecKit in your project

SpecKit is a CLI tool, not a slash-command file. You install it once per project:

```bash
# Latest install command — check https://github.com/github/spec-kit for current syntax
uvx --from git+https://github.com/github/spec-kit.git specify init
```

This creates `.specify/` in your project root with:
- `.specify/scripts/bash/` — the shell scripts the slash commands invoke
- `.specify/templates/` — the spec/plan/tasks templates
- `.specify/memory/constitution.md` — your project's non-negotiable principles

The starter kit's `speckit.*` commands assume `.specify/` exists. If it doesn't, the commands will tell you to run `specify init` first.

> **For interns:** `hello-world-ai` ships with `.specify/` already initialized so Day 1 works without an extra install step. For your own projects, run `specify init` once after `git init`.

---

## The phases

```
/speckit.constitution                                           (one-time setup)
        ↓
/speckit.specify  →  /speckit.clarify  →  /speckit.plan  →  /speckit.tasks
                                                                      ↓
                                          /speckit.analyze (read-only check)
                                                                      ↓
                                                            /speckit.implement
                                                                      ↓
                                                  /code-review → /commit → /ship
```

Plus the v0.4.5+ extensions: `/speckit.review` (post-implementation review), `/speckit.fix` (apply fixes from review), `/speckit.assign` (delegate work with confidence scores), `/speckit.checklist` (custom checklists).

---

## `/speckit.constitution` — set the rules

**Starter kit:** no (one-time setup)
**Scope:** project

Creates or updates `.specify/memory/constitution.md` — a project-level manifest of non-negotiable principles that every spec, plan, and task generation must respect. Examples:

- "We use TypeScript strict mode"
- "We require 80% test coverage on new code"
- "We never store session tokens in localStorage"
- "All endpoints must have OpenAPI contracts before implementation"

Run once per project at setup. Re-run when a principle changes (it auto-increments a semver version and propagates to templates).

---

## `/speckit.specify <description>` — start a feature

**Starter kit:** YES (one of the 10)
**Scope:** project

Takes a natural-language feature description and creates:
- A new git branch named `NNN-<short-name>` (auto-numbered, scanned across remote/local/specs to avoid collisions)
- A `spec.md` file in `specs/NNN-<short-name>/`

The command does heavy lifting:
1. Generates a 2-4 word short name from your description
2. Finds the highest existing feature number across remote branches, local branches, and specs/ directory
3. Creates the branch and the spec stub via `.specify/scripts/bash/create-new-feature.sh`
4. Loads `.specify/templates/spec-template.md`
5. Fills the template, making **informed guesses** for ambiguous areas (max 3 `[NEEDS CLARIFICATION]` markers, prioritized by impact: scope > security > UX > technical detail)
6. Generates a `requirements.md` checklist for spec quality validation
7. Iterates the spec until it passes validation (max 3 iterations)

**Example:**
```
/speckit.specify add a cookie consent modal that blocks analytics until accepted
```

Branch created: `005-cookie-consent` (or whatever the next number is). Spec at `specs/005-cookie-consent/spec.md`.

**Next:** `/speckit.clarify` (or `/speckit.plan` if the spec has zero `[NEEDS CLARIFICATION]` markers).

---

## `/speckit.clarify` — remove ambiguity

**Starter kit:** YES
**Scope:** project

Asks up to 5 targeted multiple-choice or short-answer questions to resolve underspecified areas in the current `spec.md`. Each answer is encoded directly into the spec under a `## Clarifications` section, with the actual content propagated to the appropriate spec section (Functional Requirements, Data Model, Non-Functional, Edge Cases, etc.).

**Why it matters:** Every question `/speckit.clarify` asks is a question you would have answered later via guessing, rework, or bug reports. Front-loading saves 10x downstream time.

Run BEFORE `/speckit.plan`. Skipping it means the plan bakes in assumptions, and the fix is full re-planning.

---

## `/speckit.plan` — design the implementation

**Starter kit:** YES
**Scope:** project

Reads the clarified spec + `.specify/memory/constitution.md` and generates implementation artifacts in `specs/NNN-name/`:
- `plan.md` — tech stack, architecture, file structure
- `research.md` — technical decisions and constraints
- `data-model.md` — entities, relationships, lifecycle (if applicable)
- `contracts/` — API specs (if applicable)
- `quickstart.md` — integration scenarios

This is where Claude commits to specific stack choices and file paths. Review the plan before continuing.

---

## `/speckit.tasks` — break the plan into executable tasks

**Starter kit:** YES
**Scope:** project

Reads `plan.md` + `data-model.md` + `contracts/` and generates `tasks.md`: a numbered, dependency-ordered list where each task is specific enough for an LLM to execute without extra context.

**Conventions:**
- Numbered `T001`, `T002`, ...
- Marked `[P]` if parallel-able (different files, no shared state)
- Phased: Setup → Tests → Core → Integration → Polish
- TDD order: tests before implementation within each phase

---

## `/speckit.analyze` — cross-artifact consistency check

**Starter kit:** no (optional but recommended)
**Scope:** project

**READ-ONLY.** Checks `spec.md` ↔ `plan.md` ↔ `tasks.md` for:
- **Duplication** — similar requirements phrased differently
- **Ambiguity** — vague adjectives, unresolved placeholders
- **Underspecification** — requirements missing measurable outcomes
- **Constitution alignment** — any violations of project principles
- **Coverage gaps** — requirements with zero tasks, tasks without requirements
- **Inconsistency** — terminology drift, data entities referenced in plan but not in spec

Outputs a severity-ranked findings table (CRITICAL / HIGH / MEDIUM / LOW). **Does not modify files.** You fix issues manually, or ask Claude to do it after reviewing.

---

## `/speckit.implement` — execute the tasks

**Starter kit:** YES
**Scope:** project

Reads `tasks.md` and executes each task in dependency order:
- Phases run sequentially (Setup → Tests → Core → Integration → Polish)
- Tasks marked `[P]` within a phase can run together
- Tests before implementation (TDD)
- Marks tasks as `[X]` in `tasks.md` as they complete
- Halts on failure of a non-parallel task

**After `/speckit.implement`:**
1. `/code-review` to catch issues
2. `/test` to confirm green
3. `/commit` + `/ship` to land

---

## `/speckit.checklist` — generate a custom checklist

**Starter kit:** no
**Scope:** project

Creates a custom validation checklist in `specs/NNN-name/checklists/` based on user-specified criteria. Used for things like accessibility audits, security reviews, or domain-specific quality gates.

---

## v0.4.5+ extensions

### `/speckit.review` — post-implementation review

Comments-only mode reviews the implemented feature against the spec, with batch-reject and post-merge verification options.

### `/speckit.fix` — apply review fixes

Reads `/speckit.review` output and applies the recommended fixes, with a fix-log template tracking what changed and why.

### `/speckit.assign` — delegate with confidence

Detects which tasks need human judgment, assigns confidence scores, and flags dependency-aware blockers. Useful when delegating work to multiple agents or contributors.

---

## The full flow in one block

```
# Once per project
/speckit.constitution

# Per feature
/speckit.specify "add cookie consent modal that blocks analytics until accepted"
/speckit.clarify                # answer up to 5 questions
/speckit.plan                   # plan.md + data-model.md + contracts/ generated
/speckit.tasks                  # tasks.md with T001...T012 generated
/speckit.analyze                # read-only check, fix CRITICAL findings
/speckit.implement              # code gets written, tests pass
/code-review                    # catch anything analyze missed
/test                           # confirm full suite green
/commit                         # lint + type-check + conventional commit
/ship                           # merge to main + cleanup
# /speckit.review               # optional post-merge verification
```

**Chapter 04 walks through exactly this flow on a real feature.**

---

## When NOT to use SpecKit

- **Typo fixes and one-line changes.** Overkill. Just ask Claude directly.
- **Exploratory spikes where requirements are unknown.** SpecKit assumes you can write a spec. If you can't, do a spike first, then SpecKit the thing you learned you want.
- **Refactors without behavior change.** You don't need a spec for "rename this variable across the repo."

SpecKit is for **new features** and **substantial changes**. It's the opposite of "vibe coding" — it demands you know what you want before you start.

---

## Alternatives in the spec-driven development space

SpecKit isn't the only player. Other actively-maintained SDD tools as of April 2026:

- **[Intent](https://www.augmentcode.com/tools)** — SDD-guide platform with living specs and multi-agent orchestration
- **Kiro** — alternative SDD framework with different workflow conventions
- **OpenSpec** — open spec format
- **BMAD-METHOD** — methodology + tooling combo
- **Cursor with `.cursorrules`** — minimal, IDE-integrated approach

These are *complementary*, not replacements. SpecKit is the most agent-agnostic and the best documented; the others fit different team profiles. For TSD interns, **SpecKit is the right default**. Graduate to alternatives if/when a specific need emerges.

---

## Related

- [Chapter 04 — The SpecKit Loop](../../04-the-speckit-loop/) — full end-to-end walkthrough
- [`../starter-kit/.claude/commands/speckit.specify.md`](../starter-kit/.claude/commands/speckit.specify.md) — the actual command file
- [`principles/spec-before-code.md`](../../principles/spec-before-code.md) — the underlying principle
- [github/spec-kit](https://github.com/github/spec-kit) — the upstream tool
