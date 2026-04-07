# The 27 Roles

Every role in the assembly line, what it reads, what it writes, and what it does. This is a reference page — you don't need to memorize it. Use it when you're setting up a project's `.claude/roles/` directory or when you're trying to figure out where a piece of work belongs.

---

## How roles work

Each role lives as a markdown file at `.claude/roles/<role-name>.md`. When a worker terminal runs `/prime <role>`, it loads:
1. `CLAUDE.md` (project context)
2. `.claude/roles/<role-name>.md` (this role's definition)
3. The role-specific inventory file (if any) from `.claude/inventories/`

The role file describes:
- What this role is responsible for
- What files it reads
- What files it writes
- What it does NOT do (the boundary)
- What other roles it talks to

---

## Council members (governance)

The council votes on RFCs. Major architectural decisions require council consensus. See [rfcs-and-council.md](rfcs-and-council.md) for the voting flow.

| Role | Responsibility | Council |
|---|---|---|
| **CTO** | Strategic technical direction | ✓ |
| **Architect** | Structural design decisions | ✓ |
| **Security** | Security audits and policy | ✓ |
| **Toolsmith** | Tooling, scripts, slash commands | ✓ |
| **DevOps** | CI/CD, infrastructure | ✓ |
| **ProductOwner** | Backlog priority, feature scope | ✓ |

These 6 are the council. Quorum: all non-abstaining members must approve for an RFC to pass.

---

## Strategy stage

| Role | Reads | Writes | Does |
|---|---|---|---|
| **CTO** | Roadmap, RFCs, market signals | Strategic memos, RFCs | Sets technical direction; council member |
| **ProductOwner** | Backlog, user feedback | Prioritized backlog, acceptance criteria | Feature prioritization; council member |
| **BusinessAnalyst** | Stakeholder requests | Translated requirements docs | Bridges business and engineering |

---

## Design stage

| Role | Reads | Writes | Does |
|---|---|---|---|
| **Architect** | Strategic memos, plan.md files | Architecture RFCs, decisions | Structural design; council member |
| **UXDesigner** | User research, personas | UX flow diagrams, journey maps | User experience flows |
| **UIDesigner** | UX flows, brand guidelines | Design tokens, component specs | Visual design system |

---

## Wireframes stage

The biggest stage by terminal count. Wireframe generation parallelizes well — see [wireframe-pipeline.md](wireframe-pipeline.md).

| Role | Reads | Writes | Does |
|---|---|---|---|
| **Planner** | Spec.md, screen list | Wireframe assignments | Plans which SVGs to generate |
| **Generator1** | Assigned wireframe spec | One SVG per task | Generates SVGs (`/wireframe`) |
| **Generator2** | Assigned wireframe spec | One SVG per task | Parallel generator |
| **Generator3** | Assigned wireframe spec | One SVG per task | Parallel generator |
| **PreviewHost** | SVG files | Viewer container state | Runs the hot-reload viewer |
| **WireframeQA** | SVGs, screenshots | `*.issues.md` files | Reviews SVGs, files issues |
| **Validator** | SVGs | Validator output | Runs `validate-wireframe.py` |
| **Inspector** | All SVGs in feature | Inspection report | Cross-SVG consistency check |

---

## Code stage

| Role | Reads | Writes | Does |
|---|---|---|---|
| **Developer** | Spec, plan, tasks, wireframes | Source code, unit tests | Implements features (`/speckit.implement`) |
| **Toolsmith** | Slash commands, scripts | Command files, scripts | Maintains tooling; council member |
| **Security** | Source code, dependencies | Security audit reports | Security review; council member |

---

## Test stage

| Role | Reads | Writes | Does |
|---|---|---|---|
| **TestEngineer** | Source code, requirements | E2E tests, integration tests | Writes test suites |
| **QALead** | Test results, coverage reports | Sign-off reports | Reviews coverage, signs off releases |
| **Auditor** | All artifacts | Formal audit documents | Produces audit deliverables (`/audit`) |

---

## Docs stage

| Role | Reads | Writes | Does |
|---|---|---|---|
| **Author** | Features, marketing brief | Blog posts, marketing copy | User-facing copy |
| **TechWriter** | Source code, API specs | API reference, README, runbooks | Developer-facing docs |

---

## Release stage

| Role | Reads | Writes | Does |
|---|---|---|---|
| **DevOps** | CI logs, infrastructure config | CI/CD configs, deploy scripts | Manages CI/CD; council member |
| **DockerCaptain** | Dockerfiles, compose files | Container configs | Owns container infrastructure |
| **ReleaseManager** | Test reports, sign-offs | Release notes, version tags | Cuts releases, handles rollbacks |
| **Coordinator** | Queue, all worker states | Queue updates | Internal switchboard for workers |

---

## Special role: Operator

| Role | Where it runs | Does |
|---|---|---|
| **Operator** | OUTSIDE tmux | Launches sessions, dispatches work, monitors, escalates |

The Operator is **NOT** one of the 27. It's the meta-terminal that runs the 27. See [the-operator.md](the-operator.md).

---

## Roles you might add

These aren't in TurtleWolfe's standard 27, but they show up in some projects:

- **Translator** — multilingual content
- **Designer** (separate from UX/UI) — for product design that bridges both
- **DataEngineer** — for projects with significant ETL or analytics
- **SREEngineer** — for projects with on-call rotations
- **Compliance** — for regulated industries

When you add a role, give it:
1. A definition file at `.claude/roles/<name>.md`
2. An inventory file if it needs one
3. A queue dispatcher rule (so the Operator knows when to dispatch to it)
4. A primer command if `/prime <name>` won't work out of the box

---

## Related

- [README.md](README.md) — chapter overview
- [the-assembly-line.md](the-assembly-line.md) — how the roles flow together
- [the-operator.md](the-operator.md) — the meta-orchestrator
- [dispatch-and-queue.md](dispatch-and-queue.md) — how work moves between roles
- [rfcs-and-council.md](rfcs-and-council.md) — how the 6 council members vote
