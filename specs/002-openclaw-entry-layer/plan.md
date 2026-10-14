# Implementation Plan: OpenClaw Entry Layer

**Branch**: `spec/002-openclaw-entry-layer` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/002-openclaw-entry-layer/spec.md`

**Status**: Design only. Every phase below waits for Jonathan's approval of this plan, and each phase has its own go.

## Summary

Put a cheap, always-on front door in front of Claude. Deterministic code (L0) does everything that needs no model: polling, lookups, classification, validation, dispatch. The OpenClaw gateway (L1) runs on free-tier models, cascading across providers per privacy class, and handles triage, quick answers, relays and planning-lite. Claude (L2) starts only for the escalation rows, always from a context pack. Client items skip the free models entirely. The estimate is a 15 to 27% cut in weekly use. Most of that comes from shrinking the hub session and the short sessions, and the plan says plainly that the long working sessions, 81% of the week, need context discipline rather than routing. A learning loop comes last (User Story 7). It proposes one sourced change at a time, applies nothing until Jonathan approves the card, measures each change for a week, then keeps or reverts it, and it keeps re-checking its own past changes.

## Technical Context

**Existing pieces (checked 14 Oct)**:
- OpenClaw gateway, version 2026.9.6 per local notes. It runs in its own WSL distro and listens on `ws://127.0.0.1:18789`. A Windows tray client exposes a loopback MCP server; the narrow WSL client allows four tools (notify, run, info, approvals), and every run needs Jonathan's approval.
- `lane.sh` starts lanes in tmux. Its engines are `claude`, `codex` and `copilot`. Its client guard reads `hub/client-senders.tsv`, `hub/client-repos.txt` and `~/repos/CD`, refuses the external engines on any of them, and fails closed.
- The privacy gate (`panel_gate.py`) has three classes: public, own and client. It treats an unlisted repo as client and redacts PII.
- The notes poller (`muse_poll.sh`) runs every minute from Windows Task Scheduler, with back-off. A Haiku `claude -p` pass looks for tagged drafts, and when it finds one a Sonnet pass handles it. Hatch checks every 20 minutes, 08:00 to 22:00 ET.
- The usage ledger records each panel call in `panel.jsonl` (counts and timings, no text) and Claude usage in `ledger.db`.

**New pieces (all small; no new repo)**:
- An intake queue: files in a local state folder, one per item.
- The class resolver (L0). It reads the three client lists plus the class map and returns the strictest class with every rule that matched.
- The mail fetcher (L0). It moves tagged drafts into the queue and writes reply drafts. It cannot send. It depends on open question 2.
- The entry agent (L1): an OpenClaw agent with the free chains, a prompt trimmed under 8K tokens, and four local skills (read fleet state, write a pack, queue status, route log).
- A drop folder and the dispatcher (L0). The dispatcher validates packs and calls `lane.sh`.
- A route log and a weekly report (L0).

**Language**: Python 3 for the L0 scripts, matching `~/.claude/scripts`; OpenClaw's own config format for the agent.
**Testing**: fixtures for every client signal; a fake provider that returns 429 or 5xx on demand; a replay of last week's intake in shadow.
**Constraints**: free tiers only; loopback only; no registry skills; drafts only; credentials never in a pack, log or prompt.
**Scale**: about 160 poller wakes a day today. The entry layer only calls a model when an item exists. Estimated 20 to 80 items a day, at 3 to 6 model calls each, which is 60 to 480 calls a day.

## Architecture

```
 Jonathan (tray)        Hatch (Gmail drafts)    Tower (Gmail drafts)      cron
       |                         \                    /                     |
       |                     [L0 mail fetcher, drafts only]                 |
       v                                  v                                 v
 [L0 resolver] ---------------> [ intake queue: one file per item ] <-------+
                                          |
                                  [L0 class resolver]
                       client or secret   |   public / own
              +---------------------------+--------------------------+
              v                                                      v
   [L0 pack builder, no model]                [L1 OpenClaw entry agent, free chain per class]
   (secret: quarantine instead)                 K rows: answer, relay, status, digest
              |                                 E rows and K-05: write a pack
              v                                                      v
         [ drop folder ] <-------------------------------------------+
              |
   [L0 dispatcher: validate, re-class, duplicate check] --> lane.sh (its own client guard)
              |                         |                         |
         Claude lane               Codex lane                Copilot lane
              \_______ report pack (kind: report) back to the intake queue ______/
                                          |
                               K-02 relay to Hatch or Jonathan
```

**Where things run**: the gateway stays in its own distro. The resolver, fetcher, dispatcher and ledger writers run in the main distro, beside `lane.sh`. The drop folder has to be reachable from both distros; Phase 0 picks the path (a shared WSL mount or a Windows-side folder). The agent can write packs there and do nothing else in the main distro.

**Why the dispatcher is code and not the agent**: anything that reads notes, mail and chat can be talked into things. The agent can only write a file. A script that cannot be prompt-injected decides whether that file becomes a lane, and `lane.sh` checks again.

## Constitution Check

AI_Workflow has no constitution file. The gates are the workspace rules in `~/repos/CLAUDE.md` plus this repo's non-negotiables.

| Rule | How the design meets it |
|---|---|
| Credentials never reach a model's context | FR-025 quarantine; FR-082; the mail token sits with the L0 fetcher (FR-081); the agent holds only free-provider keys |
| Email is drafts only | The fetcher has no send path. Gmail's compose scope can technically send, so the guarantee lives in the code, and that is why question 2 asks Jonathan |
| Free tiers only | FR-040 and FR-041 list the chains and the exclusions; no hop needs credit |
| Client work stays on Claude | P-01 and P-02; the resolver runs before any model (FR-024) |
| Status comes from live checks | FR-005; K-01 and K-08 cite a live source or say they couldn't check |
| One manual step at a time | Each phase below gives Jonathan exactly one step |
| Accuracy first | Shadow before authority (Phase 2); FR-031 escalates when unsure; tolerances are never loosened to pass |
| Memory, `CLAUDE.md` and routing rules change only with approval | FR-096: the learning loop can't write them, and an approved card is applied by an ordinary lane whose commit names the card |
| Find the cause and fix it for the long term | The learning loop keeps a change only if it is measured against a baseline, and it re-checks every kept change for eight weeks (FR-097, FR-099) |
| Production waits for Sunday | E-06 carries the rule; this plan touches no production |
| Docker is shared | The local model is the last hop and is used only when it is already running; the entry layer never starts it |
| Side jobs live in their primary repo | The L0 scripts go beside `lane.sh`, in the tooling repo it already lives in; no new repo |
| Lanes report in 150 words | Report packs keep the same body (FR-054) |
| AI_Workflow: no new chapter | The spec lives under `specs/`, as 001 does |

No violations, so no complexity tracking.

## Rollout

Each phase has a gate. Nothing in a later phase starts before the gate passes. Rollback at any phase: point the notes poller back at the hub and turn the entry agent off. L2 is untouched throughout, so nothing else changes.

### Phase 0: Verify and decide (no changes to any machine)

- Answer the open questions (spec, and the lane's questions file).
- Check the installed gateway version against its own docs: ordered model fallbacks, a deterministic step before the model on each channel (FR-024), loopback bind, and local-only skills. Each item gets a source link.
- Confirm each provider's free limits on its own console. This is shared with spec 001's calibration work, so it is done once.
- **Jonathan's one step**: answer question 1 (which model the gateway runs today).
- **Gate**: questions answered; a feature checklist with sources; a limits file with confirmed-on dates.

### Phase 1: L0 first, the quick win with no model

- Build the class resolver, with fixtures for every FR-021 signal, an unlisted repo, an unreadable list and a mixed public-and-client item.
- Replace the Haiku draft-check pass with a no-model check (needs question 2). If the answer is no, run the Haiku pass with a trimmed context instead, which keeps most of the gain.
- Start the route log.
- Start the learning loop's observe step, L0 only. It records weekly baselines for M1 to M3 from now on, so they exist before the entry layer changes anything. Every rollout phase from here on is written to the change log, so the loop never credits itself with what the rollout did.
- **Jonathan's one step**: approve the mail fetcher's Gmail client, or decline it.
- **Gate**: every resolver fixture passes. In the ledger, the poller's sessions drop from about 1,150 a week toward zero. Notes still arrive within Hatch's 20-minute rhythm.

### Phase 2: The entry agent in shadow

- Configure the gateway with the per-class chains, the trimmed prompt and the four local skills.
- Every item still goes to the hub as today. The agent's row, route and pack are logged beside what the hub did.
- Inject faults: a fake 429 on hops 1 and 2, then every hop.
- **Jonathan's one step**: approve the gateway config diff (model chain and skills) before it is applied.
- **Gate**: SC-001, SC-002 and SC-003. The keep share measured here replaces the assumptions in the estimate below.

### Phase 3: Live for the keep rows

- K-01, K-02, K-03, K-06 and K-08 are answered by the entry layer. The hub stops reading notes.
- E rows still reach the hub, but as packs, so the hub starts from a brief.
- **Jonathan's one step**: a yes after reading the shadow report.
- **Gate**: one week with zero false keeps reported by Jonathan or Hatch, and the hub's interactive spend down in the ledger.

### Phase 4: Live dispatch

- Turn on the drop folder and the dispatcher. K-05 goes to Codex or Copilot; E rows start Claude lanes straight from packs. The hub becomes an on-call planner (FR-057).
- Lanes write `handoff` packs before fresh restarts.
- **Jonathan's one step**: a yes after a dry-run week, in which the dispatcher logs what it would have started.
- **Gate**: SC-004 and SC-006.

### Phase 5: The tower and the gauges

- NCC-74656 gets its own gateway for its own lanes (FR-070).
- Entry ledger lines from both machines are merged for spec 001's counter, which closes spec 001's two-machine edge case.
- Optional: amend spec 001 to publish "Claude avoided" and "walls hit" dials (question 8).
- **Gate**: SC-005 and SC-007, measured on the same ledger report as the baseline.

### Phase 6: The learning loop (User Story 7)

- Starts only after Phase 4's gate has passed and one full window has gone by with no rollout change. The entry layer is the biggest change to every metric, so it gets measured before the loop proposes anything on top of it.
- Create the label set in the private workspace repo (`learning-proposal` and the state labels).
- Turn on the change log readers: watched-path git logs, the dreaming-run hashes from the tower, and the rollout phases.
- The loop files its first cards: three open at most, one per metric.
- Approved cards are applied by ordinary lanes, measured for one window, then kept or reverted. Re-checks of kept changes start the week after the first keep.
- **Jonathan's one step**: approve or reject the first card on its issue.
- **Gate**: SC-008, SC-009 and SC-010 over the first four cards. Until then, every card also goes to the hub for a second read before Jonathan sees it.

## Savings estimate

**Baseline**: the usage ledger for 7 to 14 Oct 2026, at API-equivalent prices, read on 14 Oct: $3,072. The brief's per-model figures add up to $3,057; the gap is the read time. Split by where the money went:

| Bucket | Sessions | Spend | Share |
|---|---|---|---|
| A. Lanes, long Opus sessions (200+ turns) | 9 | $1,988 | 65% |
| B. Hub, interactive Opus | 6 | $537 | 17% |
| C. Lanes, mid-length Opus sessions (10 to 199 turns) | 30 | $251 | 8% |
| D. Hub, poller passes (headless, under 10 turns) | 1,153 | $118 | 4% |
| E. Lanes, short sessions (under 10 turns) | 597 | $96 | 3% |
| F. Everything else (mid-length Sonnet, Haiku and Fable) | 49 | $82 | 3% |

**Levers and assumptions** (each range is a judgment until Phase 2 measures it):

| Lever | Applies to | Assumption | Saved per week |
|---|---|---|---|
| Polls and note handling move to L0 and L1 | D | 85 to 100% of poller spend; the few notes that need repo facts still escalate | $100 to $118 |
| Short sessions absorbed | E | 25 to 50% were triage-shaped (lookups, quick answers) | $24 to $48 |
| Hub becomes an on-call planner | B | 40 to 60% of hub work is intake, relay, status and dispatch. What stays is shorter planning sessions that start from a pack at about 10K tokens instead of growing to a 220K to 550K median | $215 to $322 |
| Lanes start from a pack | A + C | 5 to 15% fewer early discovery turns, whose output would otherwise ride in context for the rest of the session | $112 to $336 |
| **Total** | | | **$451 to $824 (15 to 27%)** |

**In terms of the weekly limit**: use tracks the limit roughly in proportion, so a week that reached 97% would land near 71 to 83%. Sessions per week fall from about 1,844 to a few hundred.

**What it doesn't fix**: 81% of the week was 14 long sessions at a median of 442K tokens per turn. Routing can't shrink those. The levers there are the existing rules (one task per session; restart fresh above about 100K) and packs make those restarts cheap and lossless. That work is outside this spec.

**What it costs**: free-tier calls (60 to 480 a day, inside Gemini's free daily allowance by third-party figures, to be confirmed in Phase 0) and a little Claude output to write report and handoff packs. The thinnest point is the own chain (Groq twice, Cloudflare, local), because Gemini can't take own items. Own items are the most likely to queue on a bad day.

**How it gets checked**: the same ledger report, by repo and by model, before and after each phase. The Phase 2 shadow log replaces the D, E and B assumptions with measured keep shares.

## Gauges feed (spec 001)

- Every free-model call the fleet makes for intake passes through the gateway, so the gateway is where free-tier use is measured. Each call writes one ledger line (FR-060, FR-061), which is the local counter spec 001 already relies on (its FR-007 and FR-008).
- The panel and the entry layer share the same free keys. The gauge shows their sum, which is also what the provider counts, so calibration still holds.
- The learning loop reads spec 001's context-load readings (its FR-029, FR-030) for M1 and M2. It takes the engine-level figures that spec 001 publishes, plus the per-lane figures that stay private.
- 429 outcomes make a "walls hit" count possible per provider. Kept-versus-escalated counts make a "Claude avoided" dial possible. Both need spec 001's allowlist amended before they publish (question 8).

## Risks

| Risk | Mitigation |
|---|---|
| Free models triage badly | Deterministic rows come first; the model can only escalate past them; shadow gate before authority |
| Free tiers shrink without notice | Five hops for public items; limits dated and flagged after 60 days; exhaustion queues instead of paying |
| The own chain is thin | Queue, not escalate; add candidate providers once confirmed (FR-041) |
| A note carries injected instructions | Notes are data; the agent can only write a file; the dispatcher is code; E-06 needs Jonathan |
| The gateway's own security record | Loopback only, no registry skills, minimal tools, exec approvals on |
| Double handling during shadow | The hub still acts; the agent only logs |
| Savings smaller than hoped | Said up front: about a fifth of the week, not most of it |
| The learning loop chases noise | A two-window baseline, a noise band, and confounded windows that are never credited (FR-098) |
| Too many cards for Jonathan | Three open at most; one per metric |
| The recursion compounds its own errors | Re-checks run against each card's original baseline, never a moving one; the loop's own settings change only through cards (FR-099) |

## Project Structure

### Documentation (this feature)

```
specs/002-openclaw-entry-layer/
├── spec.md                  # requirements, escalation table, cascade, privacy
├── plan.md                  # this file
└── contracts/
    ├── context-pack.md      # hand-off schema and worked example
    └── learning-card.md     # learning loop: metrics, card template, change log
```

`tasks.md` follows only after Jonathan approves this plan.

### Where the code would go later (not created now)

- L0 scripts (resolver, fetcher, dispatcher, route log): beside `lane.sh` in `~/.claude/scripts`, tracked in the tooling repo that already holds it.
- Entry agent config and skills: the gateway distro's own config folder (private, never in this repo).
- Packs, the intake queue and the route log: local state under `~/.claude/state/`.
