# Contract: Context Pack, version 1

The one hand-off format between layers: entry to specialist, specialist back to entry, and a lane to its own fresh restart. Spec: [../spec.md](../spec.md) FR-051 to FR-058.

**Shape**: one markdown file. YAML front matter holds the fields a machine checks; the markdown body is the brief a person or a model reads. The file is the lane's prompt file, so `lane.sh` takes it unchanged.

**Kinds**:

- `task`: entry to a specialist (Claude, Codex, Copilot) or to Hatch.
- `report`: a specialist's answer, back to the entry layer for relay (row K-02).
- `handoff`: a lane's state, written before a fresh restart above about 100K tokens of context.

## Front matter schema

```yaml
pack: 1                          # schema version; the dispatcher rejects unknown versions
id: 2026-10-14-0007              # unique; a duplicate ID is refused
kind: task                       # task | report | handoff
thread: hatch-2026-10-14-1211    # groups every pack about one ask
in_reply_to: null                # pack ID this answers (report, handoff)
created: 2026-10-14T18:02:11-04:00
built_by: entry-l1               # entry-l0 | entry-l1 | claude-lane | codex-lane | copilot-lane | hub
models_used: []                  # every model that saw the text, provider/model; empty when built by L0
source:
  channel: hatch-note            # hatch-note | tower-note | tray | chat | cron | lane-report
  received: 2026-10-14T12:11:00-04:00
class:
  value: public                  # public | own | client; the strictest match wins
  basis: []                      # every rule that matched, e.g. "classes.json: public"
route:
  to: claude                     # claude | codex | copilot | hatch | entry
  tier: opus                     # fable | opus | sonnet | haiku (claude only)
  row: E-02                      # row in the spec's escalation table
  why: ""                        # one line: the signal that decided it
  lane: ""                       # lane name for lane.sh
  dir: ""                        # working folder
ask:
  verbatim: |                    # the ask word for word; never trimmed, never paraphrased
    ...
  sha256: ""                     # hex SHA-256 of the UTF-8 bytes of verbatim as parsed; the receiver re-checks it
summary: ""                      # may be empty; sits beside the ask, never replaces it
done_when: []                    # checks that prove the work is finished
facts:                           # each one sourced and marked
  - claim: ""
    source: ""                   # path and line, command, or URL
    verified: true               # false means assumed; a fact with no source must be false
    checked: 2026-10-14
files:                           # pointers, not pastes
  - path: ""
    lines: ""                    # e.g. 108-117
    why: ""
decisions:                       # already settled; do not relitigate
  - what: ""
    by: ""
    when: ""
constraints: []                  # rules that apply to this work
open_questions: []               # for the receiver, or for Jonathan through the hub
budget:
  report_words: 150
  restart_above_tokens: 100000
return:
  report: ""                     # where the report pack goes
  relay_to: hatch                # hatch | tower | jonathan | none
state: null                      # handoff only: branch, last commit, done, next step
```

## Field rules

| Field | Required | Filled by | Limit |
|---|---|---|---|
| `pack`, `id`, `kind`, `thread`, `created`, `built_by` | always | builder | |
| `models_used` | always (may be empty) | builder | client packs: no cloud provider may appear |
| `source`, `class` | always | L0 | `class.basis` lists every match, not just the winner |
| `route` | `task` | L1 or L0 | `row` must exist in the table |
| `ask.verbatim`, `ask.sha256` | always | L0 copies the raw text | never trimmed |
| `summary` | optional | L1 (public, own), L0 or local model (client) | 120 words |
| `done_when` | `task` | L1 | at least one check |
| `facts` | `task`, `handoff` | builder | 20 entries |
| `files` | optional | builder | excerpts in the body only, 40 lines each |
| `decisions`, `constraints`, `open_questions` | `task`, `handoff` | builder | |
| `return` | `task` | L0 | |
| `state` | `handoff` | the lane | |

## Validation (the L0 dispatcher, before any lane starts)

1. Every required field is present and no unknown top-level field appears, the same allowlist discipline as spec 001.
2. `ask.sha256` matches `ask.verbatim`.
3. The resolver re-runs on the ask and the route's folder. If the class comes out stricter than the pack says, the pack is upgraded. If `models_used` then names a provider the stricter class doesn't allow, a free model has already seen text it shouldn't have: the pack is rejected, logged as a privacy misroute, and that misroute fails SC-001 and stops the rollout at its current phase. If the route is a free engine, the pack is also rejected.
4. `route.to` of `codex` or `copilot` with class `client` is rejected. `lane.sh` repeats this check.
5. The whole file is under 12K tokens (estimated as characters divided by 4). The builder trims excerpts first, then `files`, never `ask`.
6. A secret scan runs on the file. Any finding quarantines it (spec FR-025).
7. A fact with no `source` must say `verified: false`.

A rejected pack goes to the route log with its reason and the item returns to triage. It is never silently dropped.

## Body

Short sections, in this order, so a lane can start reading at the top and stop when it has enough:

1. **Goal**: one paragraph in plain words.
2. **What's known**: the facts, verified ones first.
3. **What's decided**: so the receiver doesn't reopen it.
4. **First step**: what to do in the first ten minutes.
5. **Report**: where it goes, how long, what it must contain.

## Worked example

Illustrative ask: Hatch has not sent this note. Every fact in it was checked on 14 Oct. The class is public because AI_Workflow is listed public in the class map, so the public chain applies. The first hop (Gemini) returned 429, and the second hop (Groq) triaged the item. A spec amendment is a SpecKit run, so the item matched row E-02 and went to Claude.

```markdown
---
pack: 1
id: 2026-10-14-0007
kind: task
thread: hatch-2026-10-14-1530
in_reply_to: null
created: 2026-10-14T15:31:40-04:00
built_by: entry-l1
models_used: [google/gemini-3-flash-preview, groq/openai/gpt-oss-120b]
source:
  channel: hatch-note
  received: 2026-10-14T15:30:02-04:00
class:
  value: public
  basis: ["classes.json: AI_Workflow = public"]
route:
  to: claude
  tier: opus
  row: E-02
  why: "Asks for a spec change to spec 001 (SpecKit run)."
  lane: gauges-avoided-dial
  dir: ~/repos/AI_Workflow
ask:
  verbatim: |
    Jonathan wants the gauges page to show how often the entry layer kept
    work off Claude. A "Claude avoided" dial. Can you spec it?
  sha256: 6ee3a84e23cdf8fe858f6f3cb70386f3c63de1f5363d76a464f0cb236d89aa4d
summary: "Add a 'Claude avoided' dial to the fleet gauges spec."
done_when:
  - "A PR amends specs/001-fleet-gauges/spec.md: new allowlisted field(s), an acceptance scenario, and a privacy check that the count can't reveal a repo or a client"
  - "Report pack written to the return path, 150 words or less"
facts:
  - claim: "Spec 001's published allowlist (FR-011) has no field for routing counts, so the dial needs an amendment"
    source: "specs/001-fleet-gauges/spec.md, FR-011 (branch gauges-spec)"
    verified: true
    checked: 2026-10-14
  - claim: "Spec 001 is open as PR #1 and not merged"
    source: "gh pr view 1"
    verified: true
    checked: 2026-10-14
  - claim: "Entry routing counts stay local until spec 001 allows them"
    source: "specs/002-openclaw-entry-layer/spec.md, FR-062 and User Story 5"
    verified: true
    checked: 2026-10-14
  - claim: "Ledger lines carry counts and timings only, no text"
    source: "~/.local/share/ledger/panel.jsonl line format"
    verified: true
    checked: 2026-10-14
  - claim: "The dial should show a weekly count, not a percentage"
    source: ""
    verified: false
    checked: 2026-10-14
files:
  - path: specs/001-fleet-gauges/spec.md
    lines: "FR-011 to FR-015"
    why: "The allowlist and the privacy rules the new field must pass"
decisions:
  - what: "Free tiers only; nothing paid gets a gauge (spec 001 FR-002)"
    by: Jonathan
    when: standing rule
  - what: "Aggregate numbers only; no per-repo or per-client breakdown (spec 001 FR-015)"
    by: Jonathan
    when: 2026-10-12
constraints:
  - "AI_Workflow is public: no client names, email addresses, keys or tokens"
  - "Spec only: no build"
  - "Branch off main, open a PR, don't merge"
open_questions:
  - "Weekly count, or percent of items kept?"
  - "Do dispatches to Codex or Copilot (row K-05) count as avoided?"
budget:
  report_words: 150
  restart_above_tokens: 100000
return:
  report: ~/.claude/state/lanes/2026-10-14-gauges-avoided-dial/report.md
  relay_to: hatch
state: null
---

## Goal
Amend the fleet gauges spec so the page can show how often work was kept off Claude.

## What's known
Spec 001's allowlist has no routing field; the entry layer's counts are local
only until it does. Spec 001 is open as PR #1.

## What's decided
Free tiers only, aggregate only. Don't reopen either.

## First step
Read spec 001's FR-011 to FR-015. Draft the new field and the check that it
can't reveal a repo.

## Report
150 words to the return path: PR number, the field added, open questions left.
```

### What a client pack looks like

The same schema, with different fields filled. No names here, since this repo is public:

```yaml
built_by: entry-l0
models_used: []                  # no cloud model saw it
class:
  value: client
  basis: ["client-repos.txt", "classes.json: client"]
route: {to: claude, tier: sonnet, row: P-01, why: "Client repo named in the ask."}
summary: ""                      # empty unless the local model is running
```
