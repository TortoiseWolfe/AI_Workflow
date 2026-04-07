# RFCs and the Council

How major architectural decisions get made when 27 terminals are involved. The short version: **the council votes**, the Operator dispatches, the human ratifies.

---

## The council

Six roles form the council:

| Role | Concerns |
|---|---|
| **CTO** | Strategic technical direction, long-term implications |
| **Architect** | Structural design, patterns, dependencies |
| **Security** | Threat model, secrets, compliance |
| **Toolsmith** | Tooling impact, slash command effects, automation |
| **DevOps** | CI/CD, deployment, infrastructure |
| **ProductOwner** | Roadmap fit, scope, priority |

**Quorum:** all non-abstaining members must approve. If even one rejects, the RFC fails.

---

## When to write an RFC

| Situation | RFC needed? |
|---|---|
| Adding a Stripe integration | YES — Security + DevOps + Architect all weigh in |
| Switching package managers | YES — Toolsmith + DevOps + DockerCaptain all care |
| Adding a new Next.js page | NO — that's just a feature, use the SpecKit loop |
| Renaming a CSS variable | NO — `/code-review` is enough |
| Adopting a new test framework | YES — Toolsmith + TestEngineer + DevOps |
| Restructuring `src/` directories | YES — Architect must approve |
| Adding a new slash command | NO unless it affects shared state — Toolsmith handles |
| Removing a dependency used widely | YES — Architect needs to assess blast radius |

**Rule of thumb:** if a change affects multiple roles' work, file an RFC. If it only affects one role, just do it.

---

## The RFC lifecycle

```
draft → proposed → voting → decided (passed | rejected) → implemented
```

### `/rfc <title>` — create a draft

**Access:** Council members only

```
/rfc "Payment Provider Selection"
```

Creates `docs/interoffice/rfcs/RFC-NNN-payment-provider-selection.md` with the RFC template:

```markdown
# RFC-007: Payment Provider Selection

**Status**: draft
**Author**: CTO
**Created**: 2026-04-06
**Target Decision**: 2026-04-13

## Stakeholders (Consensus Required)

| Stakeholder | Vote | Date |
|---|---|---|
| CTO | pending | - |
| Architect | pending | - |
| Security | pending | - |
| Toolsmith | pending | - |
| DevOps | pending | - |
| ProductOwner | pending | - |

## Summary

[One paragraph]

## Motivation

[Why now]

## Proposal

[Detailed solution]

## Alternatives Considered

### Alternative A: [Name]
[Description, tradeoffs]

### Alternative B: [Name]
[Description, tradeoffs]

## Impact Assessment

| Area | Impact | Mitigation |
|---|---|---|
| Codebase | [Impact] | [Mitigation] |
| Workflow | [Impact] | [Mitigation] |
| Documentation | [Impact] | [Mitigation] |

## Discussion Thread

### CTO 2026-04-06 - Initial Proposal
[Opening remarks]

## Dissent Log

| Stakeholder | Objection | Response |
|---|---|---|

## Decision Record

**Decided**: -
**Outcome**: -
```

The author fills in Summary, Motivation, Proposal, Alternatives (at least 2), and Impact Assessment.

### `/rfc-propose <number>` — move to voting

When the draft is ready, the author runs `/rfc-propose 7` to move it from `draft` to `proposed`. The Operator picks this up and dispatches `/rfc-vote 7` to all 6 council members.

### `/rfc-vote <number>` — cast a vote

**Access:** Council members only

```
/rfc-vote 7
```

The voter reads the RFC, then submits a vote: `approve`, `reject`, or `abstain`. If `reject`, they must add an entry to the Dissent Log explaining why and what they'd accept instead.

The vote updates the Stakeholders table in the RFC file.

### `/vote-now` — quick voting with auto state transitions

A faster variant for when you're caught up on the RFC and ready to vote. Reads the current voting state, shows you what's outstanding, and lets you vote on multiple at once. Detects consensus and auto-transitions the RFC to `decided` once all votes are in.

### `/council` — start a council discussion

```
/council
```

Begins a structured discussion in `docs/interoffice/discussions/`. Used when an RFC has hit a wall — votes are split and discussion is needed. Each council member adds their position; the discussion ends when the Architect or CTO calls consensus.

### `/memo <recipient> "<message>"` — send a memo

```
/memo CTO "We need to add a payment provider — Stripe vs LemonSqueezy. Can you draft an RFC?"
```

Used by non-council roles to ask council members for things. Memos go to `docs/interoffice/memos/<recipient>/<date>.md`. The recipient sees them on their next `/prep`.

### `/broadcast "<message>"` — broadcast to all roles

```
/broadcast "RFC-007 has passed. Stripe integration starts Monday."
```

Used by council members to announce decisions to everyone. Goes to `docs/interoffice/broadcasts/<date>.md`. All roles read recent broadcasts on `/prep`.

---

## A real RFC walkthrough

### Day 1 — proposal

CTO has a problem: the project needs payments. Stripe vs LemonSqueezy vs Paddle. Each has tradeoffs.

```
CTO: /rfc "Payment Provider Selection"
```

CTO drafts the RFC: summarizes the problem, proposes Stripe, lists alternatives (LemonSqueezy and Paddle) with pros/cons, fills the impact table.

```
CTO: /rfc-propose 7
```

State: `draft → proposed`. The Operator dispatches `/rfc-vote 7` to all 6 council members.

### Day 2-4 — voting

Each council member reads the RFC and votes:

- **Architect:** Approves. Stripe's API is mature, well-documented.
- **DevOps:** Approves. Stripe has the best webhook story.
- **ProductOwner:** Approves. Stripe is what users expect.
- **Toolsmith:** Approves. Existing slash commands cover Stripe well.
- **Security:** **Rejects.** Files dissent: "Stripe Connect would expose us to KYC requirements we're not ready for. Need to scope to Payment Element only, not Connect."

Status: 5/6, blocked on Security.

### Day 5 — discussion

```
Architect: /council
```

The council opens a discussion. Security's concern is valid; CTO didn't intend to use Connect. The RFC is amended to explicitly scope to Payment Element only. Security re-reviews.

```
Security: /rfc-vote 7
```

Security now approves with the scoped change.

Status: 6/6, all approved.

### Day 6 — decision

The RFC auto-transitions to `decided: passed` once all votes are in. CTO broadcasts:

```
CTO: /broadcast "RFC-007 PASSED. Stripe Payment Element implementation begins this week. See RFC-007 for the scoped approach."
```

The Operator dispatches a `/speckit.specify` task to the Developer to implement the integration based on the RFC's proposal.

---

## RFC anti-patterns

| Anti-pattern | Fix |
|---|---|
| RFC has only 1 alternative | Always at least 2. "Do nothing" counts. |
| Author votes on their own RFC | Author abstains. They wrote it, they don't get to confirm it. |
| Vote without reading | Read the RFC. Vote with a reason. |
| Reject without dissent log | Required. Your objection has to be actionable. |
| Council bypasses the queue | All RFC dispatch goes through the Operator. Don't sneak. |
| Implementing before the RFC passes | Don't. The point is consensus, not theater. |

---

## Related

- [README.md](README.md) — chapter overview
- [roles.md](roles.md) — who's on the council
- [the-operator.md](the-operator.md) — how the Operator dispatches votes
- [dispatch-and-queue.md](dispatch-and-queue.md) — the queue protocol
