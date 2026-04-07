# Dispatch and Queue

The orchestration primitives. How work moves from "I have a thing to do" to "a worker is doing it." The shared file is `.terminal-status.json` — every worker reads it; only the Operator and a few specific roles write it.

---

## The state file

```bash
.terminal-status.json
```

Schema:

```json
{
  "lastUpdated": "2026-04-06T20:30:00Z",
  "queue": [
    {
      "feature": "005-cookie-consent",
      "svg": null,
      "action": "GENERATE",
      "reason": "Planner completed assignment",
      "assignedTo": "WireframeGenerator1"
    },
    {
      "feature": "006-dark-mode",
      "svg": null,
      "action": "REVIEW",
      "reason": "All 3 SVGs ready",
      "assignedTo": "WireframeQA"
    }
  ],
  "completedToday": [
    "Generator1: Completed 005-cookie-consent (3 SVGs)"
  ]
}
```

`queue` is the active work. `completedToday` is a daily log.

---

## `/dispatch` — assign a task

**Access:** Coordinator, CTO, Architect (task assignment authority)

```
/dispatch [terminal] [feature] [action] "[reason]"
```

Example:
```
/dispatch generator-1 003-user-auth GENERATE "Plan complete - 4 SVGs assigned"
/dispatch reviewer 001-wcag REVIEW "Generator-1 completed 3 SVGs"
/dispatch inspector 005-security INSPECT "Review complete - check consistency"
/dispatch planner 008-blog PLAN "Next feature in IMPLEMENTATION_ORDER"
```

Validates terminal name, validates action, adds an entry to `.terminal-status.json`'s `queue` array, updates `lastUpdated`. Reports a queue position.

**Valid actions:**

| Action | Description | Typical assignees |
|---|---|---|
| `PLAN` | Analyze spec, create assignments | planner |
| `GENERATE` | Create SVG wireframes | generator-1/2/3 |
| `REVIEW` | Screenshot and document issues | reviewer |
| `INSPECT` | Cross-SVG consistency check | inspector |
| `IMPLEMENT` | Convert spec/wireframe to code | implementer |
| `AUDIT` | Cross-artifact consistency check | auditor |
| `TEST` | Run test suites | tester |
| `DOCUMENT` | Write documentation | author, tech-writer |

---

## `/queue` — list and manage the queue

**Access:** anyone (read), Coordinator/CTO/Architect (write)

```
/queue                              # List all queue items
/queue list                         # Same as above
/queue list [terminal]              # Filter by assigned terminal
/queue add [terminal] [feature] [action] "[reason]"   # Same as /dispatch
/queue remove [index]               # Remove by 1-based position
/queue clear                        # Clear entire queue (asks for confirmation)
```

`/queue` is the read-friendly UI for `.terminal-status.json`. `/dispatch` is the write-friendly UI for adding items.

---

## `/queue-check` — what's MY work?

**Access:** anyone (read)

```
/queue-check                        # Show all items
/queue-check [terminal]             # Show only items for that terminal
```

Used by individual workers at the start of their session to find out what's been queued for them.

```
/queue-check Developer
```

Output:
```
TASKS FOR: Developer (2 items)
1. 005-cookie-consent IMPLEMENT — wireframes approved, ready to code
2. 008-blog IMPLEMENT — spec.md ready, no wireframes needed
```

---

## `/next` — pick up the next task

**Access:** anyone (read)

```
/next
```

The worker's "what should I do?" command. Reads `.terminal-status.json`, finds the first item assigned to the current terminal's role, and reports it.

If nothing is queued, reports `No work assigned. Idle.` — the Operator should see this and dispatch.

---

## `/log` — record a finding to the central log

**Access:** anyone (write to log file)

```
/log "<message>"
```

Persists a finding to a central log file (`docs/interoffice/log/<date>.md`) so it survives the worker's `/clear`. Used when you discover something important and want to make sure it's not lost when the worker rotates.

The Operator reads the log file periodically to catch surfaced findings.

---

## `/status` — overall project health

**Access:** anyone (read)

Shows the high-level dashboard:
- Queue depth
- Workers idle vs busy
- RFCs pending vote
- Recent completions
- Stale items (items in queue > 1 hour with no assignee touching them)

This is the Operator's main monitoring command.

---

## `/refresh-inventories` — rebuild inventory files

**Access:** Toolsmith, Architect

Rebuilds the inventory files in `.claude/inventories/` from current codebase state. Inventories include:
- `dependency-graph.md` — who imports whom
- `security-touchpoints.md` — every place that handles auth, secrets, network
- `skill-index.md` — every slash command and its description
- `workflow-status.md` — CI/CD state
- `acceptance-criteria.md` — every spec's acceptance criteria
- `screen-inventory.md` — every screen in the wireframe pipeline

Workers `/prime` against these inventories. Stale inventories cause workers to operate on out-of-date assumptions. Refresh weekly, or after major refactors.

---

## `/review-queue` — show items pending review

**Access:** anyone

```
/review-queue
```

Shows items in the queue with `action: REVIEW`, plus the age of the corresponding `*.issues.md` files. Used by the WireframeQA / Inspector / Auditor roles to find what needs review attention.

---

## A typical work cycle

```
# Operator launches session
./scripts/tmux-session.sh --all

# Operator dispatches initial work
./scripts/tmux-dispatch.sh --queue
# (which internally runs `/dispatch` for each queue item from a backlog file)

# Each worker terminal runs `/prime [role]` then `/next`
# Workers do work, mark items complete, queue follow-up work

# Operator monitors with `/status` periodically
/status

# Operator escalates blockers to the human
# (e.g., "WireframeQA found a CRITICAL accessibility issue, needs your call")

# When done:
tmux kill-session -t scripthammer
```

---

## Common queue patterns

| Pattern | What it looks like | Why |
|---|---|---|
| **Fan-out** | Planner → 3 Generators in parallel | Wireframe generation parallelizes |
| **Fan-in** | 3 Generators → 1 WireframeQA | Review needs the full set |
| **Pipeline** | Spec → Plan → Tasks → Code → Test → Docs → Ship | Sequential dependencies |
| **Council vote** | RFC dispatched to 6 council members in parallel | Voting is independent |
| **Audit sweep** | Auditor dispatched to N areas in parallel | Audits don't share state |

The queue handles all of these. The action types (`GENERATE`, `REVIEW`, `INSPECT`, etc.) tell the worker what kind of work to do.

---

## Anti-patterns

| Anti-pattern | Why it's wrong |
|---|---|
| One worker assigns work to itself | Use the Operator. Workers are workers, not coordinators. |
| Dispatching without a `reason` | The reason is the audit trail. Without it, future-you doesn't know why. |
| Editing `.terminal-status.json` by hand | Use `/queue` and `/dispatch`. They keep the schema valid. |
| Filling the queue with 50 items at once | Dispatch in waves. The Operator monitors and re-dispatches. |
| Ignoring `/log` entries | The log is where workers escalate. If you don't read it, you miss findings. |

---

## Related

- [README.md](README.md) — chapter overview
- [the-operator.md](the-operator.md) — who runs all of this
- [the-assembly-line.md](the-assembly-line.md) — the 7-stage pipeline
- [rfcs-and-council.md](rfcs-and-council.md) — when work needs council approval
