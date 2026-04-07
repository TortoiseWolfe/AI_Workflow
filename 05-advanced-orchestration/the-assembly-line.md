# The 7-Stage Assembly Line

The 27 terminals aren't a flat list — they're organized into 7 pipeline stages. Work flows through the stages in order, and each stage feeds the next.

---

## The pipeline

```
Strategy  →  Design  →  Wireframes  →  Code  →  Test  →  Docs  →  Release
```

| Stage | Roles | What flows in | What flows out |
|---|---|---|---|
| **Strategy** | CTO, ProductOwner, BusinessAnalyst | Business goal, market input | Strategic direction, prioritized features |
| **Design** | Architect, UXDesigner, UIDesigner | Strategic direction | Architecture decisions, UX flows, design system tokens |
| **Wireframes** | Planner, Generator1/2/3, PreviewHost, WireframeQA, Validator, Inspector | Design decisions | Approved SVG wireframes ready for coding |
| **Code** | Developer, Toolsmith, Security | Wireframes + plan | Implemented features with tests |
| **Test** | TestEngineer, QALead, Auditor | Implemented code | Verified, audited, passing test suite |
| **Docs** | Author, TechWriter | Verified features | User-facing docs, API references, changelogs |
| **Release** | DevOps, DockerCaptain, ReleaseManager, Coordinator | Documented + tested code | Shipped to production |

Each stage has 2-7 roles. Each role is its own Claude Code terminal in the tmux session.

---

## Strategy stage

**Roles:** CTO, ProductOwner, BusinessAnalyst

The CTO sets technical direction. The ProductOwner prioritizes the backlog. The BusinessAnalyst translates between business asks and technical specs.

**Inputs:** Business goals, market signals, user feedback
**Outputs:** A prioritized roadmap, strategic decisions on stack/platform/scope

In a small project, you skip this stage entirely. In a real product with stakeholders and a roadmap, the Strategy stage runs continuously in the background — the ProductOwner terminal lives for weeks, getting periodic updates and producing dispatched work for downstream stages.

## Design stage

**Roles:** Architect, UXDesigner, UIDesigner

The Architect makes structural decisions (microservices vs monolith, what storage, what queue). The UXDesigner sketches user flows. The UIDesigner picks colors, type, components.

**Inputs:** Strategic direction from Strategy stage
**Outputs:** Architecture decisions (often in RFCs — see [rfcs-and-council.md](rfcs-and-council.md)), wireframes-to-be (handed off to the Wireframes stage)

The Architect is also a council member — meaning they vote on RFCs along with CTO, Security, Toolsmith, DevOps, and ProductOwner. Major architectural changes require council consensus.

## Wireframes stage

**Roles:** Planner, Generator1, Generator2, Generator3, PreviewHost, WireframeQA, Validator, Inspector

This is the **biggest** stage by terminal count because wireframe generation parallelizes well — one Planner assigns work to 3 Generators, who produce SVGs in parallel.

**Inputs:** Design decisions, screen list
**Outputs:** Validated, reviewed, inspected SVG wireframes ready to be coded against

Full pipeline:
1. **Planner** reads the spec and produces wireframe assignments
2. **Generator1/2/3** each pick up one assignment from the queue and produce an SVG (`/wireframe`)
3. **PreviewHost** runs the viewer container so reviewers can see the SVGs in a browser (`/hot-reload-viewer`)
4. **WireframeQA** screenshots the SVGs and writes issues files (`/wireframe-screenshots`, `/wireframe-review`)
5. **Validator** runs `validate-wireframe.py` against each SVG and flags rule violations
6. **Inspector** does cross-SVG consistency checks (do they share the same header? same color palette? same callout style?)

The 11 wireframe commands (`wireframe`, `wireframe-plan`, etc.) live in this stage. See [wireframe-pipeline.md](wireframe-pipeline.md).

## Code stage

**Roles:** Developer, Toolsmith, Security

The Developer writes feature code. The Toolsmith maintains tooling (slash commands, validators, CI scripts). The Security role audits for vulnerabilities and is a council member.

**Inputs:** Approved wireframes + spec/plan/tasks (from a SpecKit run, see Chapter 04)
**Outputs:** Implemented features, passing unit tests

This is where most of the actual *coding* happens. The Developer is one terminal — but it's running `/speckit.implement`, which is itself running the SpecKit loop on tasks generated in the Design stage.

## Test stage

**Roles:** TestEngineer, QALead, Auditor

The TestEngineer writes E2E and integration tests. The QALead reviews coverage and signs off on releases. The Auditor produces formal audit documents (security audit, accessibility audit, compliance audit).

**Inputs:** Implemented features
**Outputs:** Verified test suite, audit documents

The Auditor uses `/audit` to produce formal audit deliverables — these are the documents that go to stakeholders (or in regulated industries, to auditors).

## Docs stage

**Roles:** Author, TechWriter

The Author writes user-facing copy (blog posts, marketing). The TechWriter writes developer-facing docs (API reference, README, runbooks).

**Inputs:** Verified features
**Outputs:** Markdown files in `docs/`, blog posts, changelog entries

## Release stage

**Roles:** DevOps, DockerCaptain, ReleaseManager, Coordinator

The DevOps terminal handles CI/CD. The DockerCaptain owns container infrastructure. The ReleaseManager cuts releases and handles rollbacks. The Coordinator is the meta-role that talks to the human operator and dispatches new work.

**Inputs:** Documented, tested features
**Outputs:** Shipped releases

The Coordinator is **not** the Operator — see [the-operator.md](the-operator.md) for the difference. The Coordinator runs *inside* tmux as a worker; the Operator runs *outside* tmux as the meta-orchestrator.

---

## How work flows

A typical feature lifecycle:

1. **Operator** (outside tmux) launches the session and dispatches to **Coordinator**
2. **Coordinator** queues a task for **ProductOwner**
3. **ProductOwner** writes a feature spec, queues for **Architect**
4. **Architect** produces a plan (potentially via `/rfc` for major decisions), queues for **Planner**
5. **Planner** produces wireframe assignments, queues for **Generator1/2/3**
6. **Generators** produce SVGs in parallel, queue for **WireframeQA + Validator + Inspector**
7. After approval, **Coordinator** queues for **Developer**
8. **Developer** implements the feature (running its own `/speckit.implement`)
9. **TestEngineer** writes tests, **QALead** reviews
10. **Author + TechWriter** document
11. **DevOps + DockerCaptain + ReleaseManager** ship
12. **Coordinator** reports back to **Operator**, **Operator** reports to human

A medium feature: 2-4 hours of wall-clock time, 27 terminals doing pieces in parallel. **You** drink coffee.

---

## When this falls apart

The assembly line is fragile. Common failure modes:

| Failure | Symptom | Fix |
|---|---|---|
| Stuck on permission prompt | A worker is waiting for `y/n/always` | Find it (`tmux capture-pane`), approve manually |
| Queue is empty but a worker is idle | Worker has no work to do | Operator dispatches more |
| Circular dependency | Two workers waiting on each other's output | Operator unblocks one, restarts the chain |
| Worker context is full | Worker can't read the next task | Worker should run `/clear` + `/prime [role]`, but might be stuck |
| Wrong worker assigned | A wireframe task went to Developer | Operator re-dispatches |

The Operator's job is to **monitor** and **unblock** — see [the-operator.md](the-operator.md).

---

## Related

- [the-operator.md](the-operator.md) — the meta-terminal that runs the assembly line
- [roles.md](roles.md) — full role-by-role breakdown
- [dispatch-and-queue.md](dispatch-and-queue.md) — how work moves between stages
- [wireframe-pipeline.md](wireframe-pipeline.md) — the most parallel stage in detail
- [when-this-helps.md](when-this-helps.md) — when to actually use this
