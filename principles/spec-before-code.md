# Principle — Spec Before Code

> **Rule:** For any non-trivial change, write the spec first. Run `/speckit.specify` before you write the code, not after.

---

## Why

### The war story

A "quick feature" on a side project: add a "remember me" checkbox to the login form. Should take an hour.

The dev skipped the SpecKit loop. "It's a checkbox. I know what I want."

What actually happened:

1. **30 minutes:** Built the checkbox UI, wired it to the form state, submitted the value to the API.
2. **Hit the first question:** what does "remember me" *do*? Extend session length? Persist a refresh token? Keep the user signed in across browser restarts?
3. Picked an answer (longer session length) and built it.
4. **Next question:** how long? Picked 30 days.
5. **Hit security:** if "remember me" is on a public computer, that's a vulnerability. Should the cookie have a `Secure` flag? `HttpOnly`? `SameSite=Strict` or `Lax`?
6. Researched. Picked a stack. Built it.
7. **Next question:** what about logout? Does logout invalidate the long session, or just clear the local state?
8. Built logout. Tested. **The long-session token still worked from another browser.** Had to add a server-side revocation list.
9. Added a revocation list table. Migration. Wired it up.
10. **Next question:** what about password change? Does that invalidate existing remember-me sessions?
11. Yes, obviously. Added that to the password change handler.
12. **Next question:** GDPR? Is "remember me" a tracking technology that needs consent? Yes, in some jurisdictions. Added a consent banner.
13. Tests broke. Fixed them. Some accessibility tests broke. Fixed them.
14. **Final state:** 4.5 hours, 14 files touched, 3 commits, no spec, no clear answer to any of the questions above documented anywhere.

Six months later, a new contributor asked: "Why does logout sometimes leave a remember-me cookie alive?" Nobody remembered the rationale. The answer was buried in a closed PR that didn't have meaningful comments.

The dev wrote a postmortem. The postmortem said:

> "The feature is correct but undocumented. Future me has no idea why these decisions were made. Everything I learned along the way (the security questions, the GDPR question, the revocation strategy) had to be re-learned by reading the code. A 60-second `/speckit.specify` run at the start would have surfaced all these questions in the **spec** instead of in the **code review**, and would have left an artifact that explained the decisions in 2026 to future me in 2027."

Estimated time savings if the spec had been written first: **2.5 hours** (5x less rework, plus the questions would have been answered as design choices, not bug fixes).

### The general principle

The reason "spec before code" works is:

1. **Writing the spec forces you to make decisions explicit.** The "remember me" example had 8 questions hiding in a 5-word feature description. The spec exposes all of them.

2. **Decisions made on paper are 100x cheaper to change** than decisions made in code. Want to change "30 days" to "14 days"? Edit one line in the spec vs. refactoring a migration, the cookie expiry logic, and the test fixtures.

3. **The spec is the audit trail.** When future-you (or future-someone-else) asks "why is this 30 days and not 7?", the spec has the answer. Code rarely does.

4. **Constraints surface early.** "Should this feature respect GDPR?" is a question you want to answer in the spec, not in code review when you're already 4 hours in.

5. **The human stays in the loop.** Without a spec, you ask Claude to "build a login feature" and Claude makes 50 invisible decisions on your behalf. With a spec, you make those decisions consciously.

This isn't about formality. It's about **front-loading the questions** so you spend your coding time *coding*, not *deciding*.

---

## How to apply

### The rules

1. **For typo fixes and one-liners:** skip the spec. Just code.

2. **For bug fixes:** write a one-paragraph spec capturing the repro and the acceptance criteria. Use `/speckit.specify` to generate it. The spec is your bug report + your "done" definition.

3. **For small features (< 5 files):** run `/speckit.specify` + `/speckit.plan`, then code. Skip clarify/tasks/analyze.

4. **For medium features (5-20 files):** full SpecKit loop. `/speckit.specify` → `/speckit.clarify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.analyze` → `/speckit.implement`.

5. **For large features:** full loop, plus `/speckit.checklist` for custom validation gates.

6. **The decision tree** is in [`04-the-speckit-loop/when-to-use-what.md`](../04-the-speckit-loop/when-to-use-what.md).

### How long is the spec?

A small spec is 30-50 lines. A medium spec is 100-200 lines. A large spec is 200-400 lines. The spec is **not** the documentation — it's the requirements + acceptance criteria. Documentation comes later in the docs stage.

If your spec is over 500 lines, you probably have a multi-feature change. Split it into multiple specs.

If your spec is under 30 lines, you may not need one — consider just running `/speckit.specify` to capture the bare minimum and then proceeding directly to code.

### What goes in the spec

- **Functional Requirements** — what the feature does, testably
- **User Stories** — who wants this and why
- **Success Criteria** — measurable outcomes (time, percentage, count)
- **Out of Scope** — what this feature does NOT do (just as important)
- **Non-Functional Requirements** — performance, accessibility, security
- **Open Questions** — anything `/speckit.clarify` should resolve

What does NOT go in the spec:
- Implementation details (those go in the plan)
- Code (that comes after `/speckit.implement`)
- Marketing copy (that goes in the docs stage)

---

## When NOT to apply

- **Typo fixes.** Don't spec a typo.
- **Renames.** A rename across files is mechanical; just do it.
- **Dependency upgrades.** The upgrade IS the change; no spec needed.
- **Reverting a commit.** The commit being reverted IS the spec.
- **Exploratory spikes.** You don't know what you want yet. Spike, learn, then SpecKit the result.

---

## The honest tradeoff

`/speckit.specify` takes ~5 minutes. `/speckit.clarify` adds another 5. `/speckit.plan` adds another 5. So a small feature has ~15 minutes of overhead before you write a line of code.

That feels like a lot when you're "just trying to add a checkbox."

The math: if the spec saves you even 30 minutes of rework downstream (by surfacing one question that would have caused a refactor), it paid for itself 2x. The "remember me" example saved 2.5 hours — the spec would have paid for itself 10x.

**Most features are like "remember me."** They look small. They have hidden questions. The spec exposes the questions while they're cheap.

---

## Related

- [Chapter 04 — The SpecKit Loop](../04-the-speckit-loop/) — the full workflow
- [`04-the-speckit-loop/walkthrough.md`](../04-the-speckit-loop/walkthrough.md) — the loop on a real feature
- [`04-the-speckit-loop/when-to-use-what.md`](../04-the-speckit-loop/when-to-use-what.md) — when to skip vs when to use
- [`03-slash-commands/catalog/speckit.md`](../03-slash-commands/catalog/speckit.md) — the SpecKit command reference
