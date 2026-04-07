# The Wireframe Pipeline

11 commands, 8 roles, one validator script, one viewer container. The most parallel stage of the assembly line. Used in production on ScriptHammer to generate WCAG-compliant SVG wireframes for 50+ features.

This page describes the *flow*. For per-command details, read the actual command files at `~/repos/Claude_Commandz/global/.claude/commands/wireframe*.md` after running `install-full-kit.sh`.

---

## Why SVG wireframes?

Three reasons:

1. **Version-controllable.** SVGs are text. They diff cleanly. They live in git alongside the code they describe.
2. **Validatable.** A Python script (`validate-wireframe.py`) parses the SVG, walks the elements, and enforces 30 rules: minimum font size, color palette, accessibility safe areas, etc. Validation is mechanical.
3. **Linkable.** Each wireframe annotation can be hyperlinked to a Functional Requirement (`FR-001`), a User Story (`US-001`), or a Success Criterion (`SC-001`) — the wireframe IS the spec.

The downside: generating good SVGs is non-trivial. Hence the 11-command pipeline.

---

## The 11 commands

| Command | Stage | Role | Does |
|---|---|---|---|
| `/wireframe-plan` | Planning | Planner | Reads spec, produces wireframe assignments |
| `/wireframe-prep` | Planning | Planner | Loads wireframe context for a feature |
| `/wireframe` | Generation | Generator1/2/3 | Produces ONE SVG (the main command) |
| `/wireframe-focused` | Generation | Generator1/2/3 | Generates SVG with focused/single-context input |
| `/hot-reload-viewer` | Preview | PreviewHost | Starts the viewer container at localhost:3000 |
| `/viewer-status` | Preview | PreviewHost | Health check on the viewer container |
| `/wireframe-screenshots` | Review | WireframeQA | Takes standardized screenshots of SVGs |
| `/wireframe-review` | Review | WireframeQA | Reviews SVGs, finds issues, classifies as PATCH or REGEN |
| `/wireframe-fix` | Fix | Generator1/2/3 | Auto-loads context and applies targeted fixes |
| `/wireframe-inspect` | Inspect | Inspector | Cross-SVG consistency checker |
| `/wireframe-status` | Tracking | All | Updates wireframe status (interactive menu) |

11 commands, 1421 total lines in the live versions. The flagship `/wireframe` command alone is 600+ lines because SVG generation has so many rules.

---

## The flow

```
spec.md
  │
  ▼
/wireframe-plan      ──────► wireframe assignments (in queue)
  │
  ▼
/dispatch fan-out ──┐
  │                  │
  │           /wireframe (Generator1) ──► SVG #1 ──┐
  │           /wireframe (Generator2) ──► SVG #2 ──┤
  │           /wireframe (Generator3) ──► SVG #3 ──┘
  │                                           │
  │                                           ▼
  │                              /hot-reload-viewer (PreviewHost)
  │                                           │
  │                                           ▼
  │                              /wireframe-screenshots (WireframeQA)
  │                                           │
  │                                           ▼
  │                              /wireframe-review (WireframeQA) ──► *.issues.md
  │                                           │
  │                                  ┌────────┴────────┐
  │                                  ▼                 ▼
  │                          PATCH classified    REGEN classified
  │                                  │                 │
  │                                  ▼                 ▼
  │                          /wireframe-fix     /wireframe (regen)
  │                                  │                 │
  │                                  └────────┬────────┘
  │                                           ▼
  │                              /wireframe-inspect (Inspector)
  │                                           │
  │                                           ▼
  │                              cross-SVG consistency report
  │                                           │
  │                                           ▼
  └────────────────────────────────►  approved wireframes ──► Code stage
```

---

## The validator

The pipeline rests on `validate-wireframe.py` — a Python script that parses the SVG, walks the elements, and enforces 30 rules. Examples:

- **`MOBILE-001`** — Mobile content y >= 78 (after header safe area)
- **`BTN-001`** — Buttons must use approved fill colors
- **`G-022`** — Canvas background must be the blue gradient
- **`G-024`** — Title block required at y=28
- **`G-025`** — Signature required at y=1060
- **`G-034`** — Mobile content within safe area
- **`G-035`** — Buttons must have solid fills
- **`G-036`** — Badges must stay within container bounds
- **`G-037`** — Annotation titles bold, dark text colors

Generators run the validator before reporting completion. The Validator role runs it again as a double-check. If validation fails, the Generator must fix it — **never bypass the validator**, never claim "this is a false positive."

---

## The viewer

A Docker container that serves the SVGs at `http://localhost:3000` with hot reload. The PreviewHost role starts and monitors it. The container watches the wireframes directory and reloads when an SVG is added or changed.

```
/hot-reload-viewer       # start
/viewer-status           # health check
```

WireframeQA uses the viewer to take screenshots and visually review the SVGs. Inspector uses it to compare multiple SVGs side by side for consistency.

---

## Issues files

Each SVG can have a sibling issues file:

```
docs/design/wireframes/005-cookie-consent/01-modal-flow.svg
docs/design/wireframes/005-cookie-consent/01-modal-flow.issues.md
```

The issues file contains the WireframeQA's findings, classified:

| Classification | What it means |
|---|---|
| **PATCH** | Small fix — apply during regeneration without rebuilding |
| **REGEN** | Layout-level issue — incorporate feedback into a new generation |
| **COVERAGE** | Missing FR/SC group — add to annotations |

**Critical rule: NEVER delete `.issues.md` files.** They're historical documentation. They record review findings, audit trail for quality improvements, and references for recurring patterns. When regenerating an SVG, READ the issues file, ADDRESS the issues, KEEP the file (optionally add "Resolved: YYYY-MM-DD" notes).

---

## Why this is a separate stage

A small project doesn't need this. You write a feature, you build the UI as you go, you ship. No wireframes, no validator, no viewer.

The wireframe pipeline pays off when:

- **You have 20+ screens** that need to be consistent
- **You have a strict design system** (color palette, type scale, accessibility rules) that has to be enforced mechanically, not by human review
- **Multiple developers will build the same screens** and you need a single source of visual truth
- **Compliance matters** (WCAG AAA, government accessibility standards) and you need an auditable artifact

For ScriptHammer (a production PWA template with 50+ features and WCAG compliance requirements), the pipeline is essential. For a side project, it's overkill — just code the UI directly.

---

## How to set this up in your own project

**Don't, until you're sure you need it.** But if you do:

1. **Clone the validator script** from a project that has it. ScriptHammer has `docs/design/wireframes/validate-wireframe.py` and `docs/design/wireframes/templates/{light,dark}-theme.svg`. Adapt the rules to your design system.

2. **Set up the viewer container.** Look at ScriptHammer's `docs/design/wireframes/index.html` and the surrounding files for the hot-reload viewer setup.

3. **Run `install-full-kit.sh`** to install the 11 wireframe commands globally.

4. **Create role files** for Planner, Generator1/2/3, PreviewHost, WireframeQA, Validator, Inspector at `.claude/roles/`.

5. **Update `scripts/tmux-session.sh`** to launch these roles in the assembly line.

6. **Test with a single feature** before scaling. Generate 1 SVG end-to-end through the pipeline before fanning out.

The first feature takes hours to set up. The 50th feature takes 20 minutes — that's where the pipeline pays back.

---

## Related

- [README.md](README.md) — chapter overview
- [the-assembly-line.md](the-assembly-line.md) — where wireframes fit in the 7-stage pipeline
- [roles.md](roles.md) — the 8 roles in this stage
- [dispatch-and-queue.md](dispatch-and-queue.md) — how wireframe work moves through the queue
- ScriptHammer's wireframe directory (reference implementation)
