# Chapter 04 — The SpecKit Loop

**Day-1 question:** *"How do I ship a whole feature without getting lost?"*
**Time budget:** 60 minutes
**You'll finish with:** A real feature shipped end-to-end through the 10-command SpecKit loop, with a spec, plan, tasks, code, tests, and a merged commit on main.

---

## Day-1 minimum: the loop in one diagram

```
/speckit.constitution               (one-time per project)
       │
       ▼
/speckit.specify "feature description"
       │
       ▼
/speckit.clarify                    (up to 5 questions, optional but recommended)
       │
       ▼
/speckit.plan                       (architecture, file layout, contracts)
       │
       ▼
/speckit.tasks                      (numbered, dependency-ordered)
       │
       ▼
/speckit.analyze                    (read-only consistency check)
       │
       ▼
/speckit.implement                  (code gets written)
       │
       ▼
/code-review                        (catch what analyze missed)
       │
       ▼
/test                               (full suite green)
       │
       ▼
/commit  →  /ship                   (land on main)
```

10 commands. One feature. ~60 minutes for a small feature, hours-to-days for a large one. The discipline doesn't change with size.

**Go straight to:** [walkthrough.md](walkthrough.md) — a complete worked example using a real feature (cookie consent modal) from `/speckit.constitution` through `/ship`.

Then do the [exercise](exercise.md).

---

## Why a loop instead of "just ask Claude to build it"

The shortest path between "I want a feature" and "the feature exists" is:

```
Tell Claude what you want → Claude writes code → you commit
```

This works for **typo fixes and one-line changes**. It collapses for anything bigger because:

1. **You don't actually know what you want** until you've forced yourself to describe it in writing. The first version of any spec has gaps.
2. **Claude doesn't know what you don't know.** Without explicit constraints, Claude makes plausible-sounding guesses that compound.
3. **Code without tests becomes legacy code on day one.** Tests have to be planned, not retrofitted.
4. **Refactoring is cheap; re-architecting is expensive.** If you commit to an architecture in your head and code it up, you find out it's wrong on day three. If you commit to an architecture in `plan.md`, you find out it's wrong in 5 minutes when `/speckit.analyze` flags an inconsistency.

The SpecKit loop is **front-loaded discipline**. The 5-15 minutes you spend in `/speckit.specify` + `/speckit.clarify` + `/speckit.plan` + `/speckit.tasks` saves hours of rework downstream.

---

## When to use the full loop vs when to skip

| Situation | Use |
|---|---|
| Typo fix, one-line change, rename a variable | **Just ask Claude.** The loop is overkill. |
| Bug fix that needs investigation | **`/speckit.specify` only**, then code. The spec is your bug repro + acceptance criteria. |
| Small feature (< 1 day of work, < 5 files) | **`/speckit.specify` → `/speckit.plan` → code.** Skip clarify, tasks, analyze. |
| Medium feature (1-3 days, 5-20 files) | **Full loop**, including clarify and analyze. |
| Large feature, refactor, or architectural change | **Full loop, plus `/speckit.checklist`** for custom validation gates. |
| Exploratory spike — you don't know what you want | **Skip the loop entirely.** Spike first. Then SpecKit the thing you learned you want. |

The full loop has overhead. Use it where the overhead pays for itself.

---

## Dig deeper

- [**walkthrough.md**](walkthrough.md) — the cookie consent example, end-to-end
- [**when-to-use-what.md**](when-to-use-what.md) — decision tree for matching the loop to feature size
- The 10 SpecKit commands' full reference: [`../03-slash-commands/catalog/speckit.md`](../03-slash-commands/catalog/speckit.md)
- [`principles/spec-before-code.md`](../principles/spec-before-code.md) — the underlying principle and the war story

---

## Exercise

[**exercise.md**](exercise.md) — Pick a small feature for `tsd-exercise-01` (your project from Chapter 01). Run the full SpecKit loop on it. Ship a real commit through `/commit` and `/ship`. 60 minutes.

---

**Next:** [Chapter 05 — Advanced Orchestration](../05-advanced-orchestration/) (Level 3 / Optional)
