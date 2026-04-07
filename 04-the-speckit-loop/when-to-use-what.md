# When to Use What

The full SpecKit loop is 10 commands. Sometimes you need all 10. Sometimes 3. Sometimes none. This page is the decision tree.

---

## The decision tree

```
Is the change a typo, a one-line fix, or a rename?
├── Yes → JUST ASK CLAUDE. No SpecKit. No spec. Just /commit.
└── No
    │
    Is the change a bug fix?
    ├── Yes → /speckit.specify (just to capture the repro), then code,
    │         then /code-review + /commit
    └── No
        │
        Is the change small (1 day, < 5 files, no new architecture)?
        ├── Yes → /speckit.specify → /speckit.plan → code →
        │         /code-review → /commit
        └── No
            │
            Is the change medium (1-3 days, 5-20 files)?
            ├── Yes → FULL LOOP: specify → clarify → plan → tasks →
            │         analyze → implement → code-review → commit → ship
            └── No
                │
                Large change, refactor, or new architecture?
                └── FULL LOOP + /speckit.checklist for custom validation gates
```

---

## Quantitative size guide

| Estimated effort | Files touched | New components | Use |
|---|---|---|---|
| < 30 min | 1 | 0 | Just ask Claude. No SpecKit. |
| 30 min - 2 hr | 1-3 | 0-1 | `/speckit.specify` + code + `/commit` |
| 2 hr - 1 day | 3-10 | 1-3 | `/speckit.specify` → `/speckit.plan` → code → `/code-review` → `/commit` |
| 1-3 days | 5-20 | 2-5 | Full loop |
| > 3 days | 20+ | 5+ | Full loop + `/speckit.checklist` + maybe `/speckit.taskstoissues` |

These are guidelines, not laws. **Err on the side of more SpecKit, not less.** The cost of running an unnecessary `/speckit.plan` is 30 seconds; the cost of skipping a needed one is 3 hours of rework.

---

## Qualitative signals

### Use the full loop when:

- **You're not sure what you want yet.** The loop forces you to commit.
- **More than one file will change.** Cross-file changes need a plan.
- **Tests are non-trivial.** Tests need to be planned, not retrofitted.
- **The change touches a security boundary** (auth, secrets, network egress, file uploads).
- **The change touches a public API or contract** that other code depends on.
- **You're handing this off to someone else** (or future-you in 6 months).
- **You'll need to justify the change later** (compliance, audit, postmortem).

### Skip the loop when:

- **It's a typo or obvious one-liner.** Don't perform discipline; do the work.
- **You're in an exploratory spike** and don't know what you want. Spike first, SpecKit the result.
- **The codebase is on fire and you're firefighting.** Patch first, write the spec in the postmortem.
- **You're prototyping a UI to show someone.** Throwaway prototypes don't need specs.

### Skip part of the loop when:

| Skip | When |
|---|---|
| `/speckit.constitution` | After the first run on a project. It's one-time. |
| `/speckit.clarify` | When the spec is already unambiguous (rare). |
| `/speckit.analyze` | Never skip on a real feature. Always skip on a typo. |
| `/speckit.checklist` | Default. Add it for compliance/security/accessibility-critical features. |
| `/speckit.taskstoissues` | Unless your team uses GitHub issues as a source of truth, skip. |
| `/speckit.workflow` | When you want to run the full chain end-to-end without manually invoking each step. (TurtleWolfe-authored — runs constitution → ... → implement automatically.) |

---

## The one rule that matters

**Match the discipline to the size.** A 1-line change with a 200-line spec is overhead theater. A 200-file refactor with no spec is reckless. The loop is a tool — pick the right amount.

If you're constantly skipping the full loop, you're either working on small changes (good — keep skipping) or you're being lazy (bad — start using it).

If you're constantly running the full loop on small changes, you're either being thorough (acceptable — but inefficient) or you don't trust yourself to make small changes safely (signal: you need better tests or a better lint setup).

---

## Related

- [README.md](README.md) — the loop overview
- [walkthrough.md](walkthrough.md) — the full loop on a real feature
- [exercise.md](exercise.md) — your turn
- [`../03-slash-commands/catalog/speckit.md`](../03-slash-commands/catalog/speckit.md) — per-command reference
