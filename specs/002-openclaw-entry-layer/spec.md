# Feature Specification: OpenClaw Entry Layer (free-tier front door, Claude as the specialist)

**Feature Branch**: `spec/002-openclaw-entry-layer`
**Created**: 2026-10-14
**Status**: Draft (design only: nothing is installed, configured or run on any machine until Jonathan approves the plan)
**Input**: Hatch's note of 14 Oct, relaying Jonathan: tokens are burning out again this week, so should Claude stop being the head? Put OpenClaw at the top as the always-on entry and dispatcher layer, on free models pooled across free-tier providers with a fallback chain, so the front door stays open when one provider rate-limits. The gateway daemon is not the model; it survives the model hitting a wall. Claude moves underneath as the specialist and starts only when the work needs deep planning, code, SpecKit runs or council review. Planning splits: OpenClaw does routing and planning-lite, Claude does heavy planning on a packed brief. H-7CH (Hatch) stays front of house; OpenClaw becomes the dispatcher between Jonathan's and Hatch's traffic and Claude. Free tiers only, a standing rule.

**Companion files**: [plan.md](plan.md) (architecture, rollout, savings estimate, gauges feed) and [contracts/context-pack.md](contracts/context-pack.md) (the hand-off schema with a worked example). Feeds [spec 001, fleet gauges](https://github.com/TortoiseWolfe/AI_Workflow/pull/1).

## Why now: where the week went

Usage ledger, 7 to 14 Oct 2026, at API-equivalent list price. The subscription is flat, so this is a yardstick, not money spent.

- **$3,072 across 1,844 Claude sessions.** Opus was $2,561 of it.
- **1,750 sessions ran under 10 turns and cost $214 (7%).** Most were the notes poller's headless passes. Every session, however small, starts by loading about 45K tokens of base context (median first turn; p10 24K, p90 51K) before it does anything.
- **14 sessions ran 200 turns or more and cost $2,503 (81%)**, at a median of 442K tokens of context per turn. 87% of Opus use is cache reads: long contexts re-read on every step.
- **The hub session** (the director of directors in `~/repos`) cost $537 in interactive Opus work, plus $118 in poller passes.

An entry layer can remove most sessions outright. Most of the money, though, sits in a few long working sessions that still need Claude. The plan's estimate is that flipping the stack saves roughly a fifth of the week (15 to 27%), and it says plainly what it leaves untouched.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - The front door stays open when a provider hits its wall (Priority: P0)

As Jonathan or Hatch, I send a request and get an acknowledgement within a minute, even while a free provider is rate-limiting, because the gateway is a daemon and the model is replaceable.

**Why this priority**: An entry layer that goes dark when Gemini is busy is worse than today's setup.

**Independent Test**: With a fixture that makes the first two providers in a chain return 429, an item is still triaged by the third. With every provider failing, the item is acknowledged, queued, and its status says when it will retry.

**Acceptance Scenarios**:

1. **Given** the first provider in the item's chain returns 429, **When** the item arrives, **Then** the next allowed provider handles it and the ledger records the fallback hop
2. **Given** every allowed provider is cooling down, **When** a non-urgent item arrives, **Then** it is acknowledged and queued, and it is **not** escalated to Claude (an exhausted chain queues the item; it doesn't escalate)
3. **Given** every provider is cooling down and the item is urgent (row E-12), **When** it arrives, **Then** it goes to Claude

---

### User Story 2 - Claude starts only when the work needs Claude (Priority: P0)

As Jonathan, I want status checks, relays and quick answers handled without opening a Claude session, and Claude started only for the rows in the escalation table, with a packed brief instead of a cold start.

**Why this priority**: This is where the session count and the start-up tax go away.

**Independent Test**: Replay last week's intake items (notes, requests, lane reports) through the triage in shadow mode and compare each keep-or-escalate call with what the hub actually did.

**Acceptance Scenarios**:

1. **Given** "any notes from Hatch?" or "is lane X done?", **When** asked, **Then** it is answered from a live lookup (row K-01) and no Claude session starts
2. **Given** a request to spec a feature, **When** triaged, **Then** a Claude lane starts from a context pack (row E-02), never from a bare one-line prompt
3. **Given** a code change on a public or own repo with an acceptance check, **When** triaged, **Then** it goes to a Codex or Copilot lane (row K-05), following the existing cheapest-engine rule

---

### User Story 3 - Client work never reaches a free model (Priority: P0)

As Jonathan, I need any item that involves a client to reach Claude without its text ever going to a free cloud provider.

**Why this priority**: Free tiers may train on input. A client leak cannot be undone.

**Independent Test**: Feed one item per client signal in FR-021 (and one with an unreadable list). Each is classed client by deterministic code before any model call, and the ledger shows zero free-model calls for those items.

**Acceptance Scenarios**:

1. **Given** an item matching any client signal, **When** it arrives, **Then** it is classed before any model sees it and its body is never sent to a free provider
2. **Given** an item whose class can't be determined, **When** it arrives, **Then** it is treated as client
3. **Given** a client pack, **When** inspected, **Then** its summary was written by deterministic code or the local model, and `models_used` lists no cloud provider

---

### User Story 4 - Nothing gets lost between layers (Priority: P0)

As the Claude session receiving work, I need the ask word for word, the facts with their sources, what's already decided and where to report, so I neither re-derive nor relitigate.

**Why this priority**: A cheap entry layer that hands over lossy briefs moves the cost into rework.

**Independent Test**: For 10 shadow items, start a Claude lane from the pack alone and count the questions it asks that the pack should have answered.

**Acceptance Scenarios**:

1. **Given** any pack, **When** read, **Then** it carries the ask verbatim with its hash, and the summary sits beside it, never in place of it
2. **Given** any fact in a pack, **When** read, **Then** it is marked verified or assumed and names its source
3. **Given** a lane finishes, **When** it reports, **Then** the report is a pack of kind `report`, so the entry layer can relay it without a Claude session

---

### User Story 5 - Free-tier use is measured where it happens (Priority: P1)

As the gauges dashboard (spec 001), I need one ledger line for every free-model call the entry layer makes, rate-limit hits included.

**Why this priority**: The entry layer is where free-tier traffic concentrates, so it is the natural meter.

**Independent Test**: Over a day, the gateway's own call count equals the number of new entry lines in the ledger.

**Acceptance Scenarios**:

1. **Given** an entry-layer model call, **When** it completes or fails, **Then** one ledger line is written in the existing format plus `caller` and `outcome` (FR-061)
2. **Given** a 429, **When** logged, **Then** it is countable per provider so a gauge can show "walled N times today"
3. **Given** keep-or-escalate counts, **When** recorded, **Then** they stay local until spec 001's allowlist is amended to publish them

---

### User Story 6 - The tower carries its own share (Priority: P2)

As the owner of two machines, I want NCC-74656 to run its own entry gateway for its own lanes, while NX-01 stays the only dispatcher for shared intake, so no item is ever dispatched twice.

**Independent Test**: The same note delivered to both machines produces exactly one lane.

## Requirements _(mandatory)_

### Layers

- **FR-001**: Three layers. **L0** is deterministic code with no model: pollers, lookups, the class resolver, schema checks, the dispatcher. **L1** is the OpenClaw gateway on free models: intake, triage, quick answers, planning-lite, pack building. **L2** is the specialists: Claude lanes, plus Codex and Copilot lanes, each started only from a pack.
- **FR-002**: The gateway keeps accepting, acknowledging and queueing items with no model available (L0 mode).
- **FR-003**: Jonathan can still open Claude Code directly at any time. The entry layer is the default path, never a gate on him.
- **FR-004**: Hatch keeps its role and its channel (Gmail drafts with the existing tags). What moves is the hub's job of reading, triaging and routing those notes.
- **FR-005**: Status, wrap-up and "what's left" answers come from live checks (APIs, Gmail, git, the lane index), never from model memory. An answer that couldn't check says so.

### Privacy and classification

- **FR-020**: Every item gets one class, the same three classes the review panel's privacy gate uses: `public`, `own`, `client`. The strictest class that matches wins.
- **FR-021**: Client signals, checked by L0 **before any model call**:
  1. the sender is on the client sender list (`hub/client-senders.tsv`)
  2. a repo or path named in the item is on `hub/client-repos.txt`, sits under `~/repos/CD`, or is listed `client` in the panel's class map (`~/.config/panel/classes.json`)
  3. the repo is not listed in the class map at all (unlisted counts as client, as the gate already does)
  4. a term from the gate's private terms file appears
  5. the thread or lane was already classed client (class carries forward)
- **FR-022**: One resolver reads all of those lists and returns the strictest class and every rule that matched. If any list is missing or unreadable, every item is client (fail closed, as `lane.sh` and the gate do today). Merging the three lists into one map is a separate cleanup, noted in the plan.
- **FR-023**: A model can raise a class, never lower one. If L0 matched a client signal, client wins over anything the triage model infers.
- **FR-024**: The resolver runs before the first model call on every item, whatever channel it came from. If the gateway can't run a deterministic step before its model on a given channel (Phase 0 checks this), that channel stays off and its traffic enters through the intake queue instead.
- **FR-025**: An item containing a secret (scanner finding on the raw text) is quarantined: no model sees it, Claude included, and Jonathan is told the item ID only. Credentials never reach any model's context.

### Escalation criteria

- **FR-030**: Each item takes exactly one row. Order: privacy rows (P) first, then escalation rows (E), then keep rows (K). The deterministic signals are checked first; the triage model fills in only what they leave open. The model can escalate an item, but it can never de-escalate a P or E match. Within a group, the first matching row in table order sets the route, and the constraints of every other matching row still apply: an E-06 match always means Jonathan decides, whichever row picked the lane. K-04 is the triage step itself, not a destination; an item that triage can't place on any other row goes to E-11.

| Row | Task kind | Deciding signal | Goes to |
|---|---|---|---|
| P-01 | Anything touching a client | Any FR-021 signal, matched by L0 | Claude, with the pack built by L0 |
| P-02 | Class undeterminable | No signal resolves the repo, path or sender | Treated as P-01 |
| P-03 | Contains a secret | Secret-scan finding on the raw item | Quarantine (FR-025) |
| E-01 | Writing or changing code the engine rule gives to Claude | Repo class `client`; or Codex or Copilot already failed on it; or it needs a Claude-only tool | Claude lane (Sonnet executes, Opus plans) |
| E-02 | SpecKit run | Asks for a spec, plan, tasks, analyze or implement, or a multi-item change has no spec yet | Claude (Opus; Fable for paying clients) |
| E-03 | Council or review | Asks for a council, review or stress-test, or a PR needs review before merge | Claude, with the free panel in shadow |
| E-04 | Heavy planning | Touches more than one repo, changes roadmap priorities, or needs a decision recorded for Jonathan | Claude planner on a pack |
| E-05 | Client email or client judgment | P-01 plus mail or a client decision | Claude (drafts only, voice-checked) |
| E-06 | Production, security, credentials, anything destructive or irreversible | Deploy, restart, delete, rotate, force-push, a production host, or a note asking for one | Claude, and Jonathan decides (Sunday-afternoon rule) |
| E-07 | Debugging | A failing check, stack trace or "it's broken" report on a repo | Claude lane, or Codex on public or own repos when a check reproduces it |
| E-08 | Batch of mechanical changes in one repo | Several well-specified items with checks | Claude director (it tiers its own workers) |
| E-09 | A free answer was rejected | Jonathan or Hatch pushed back on a K-row answer, or the same item came back twice | Claude |
| E-10 | Explicit ask | Jonathan names Claude | Claude |
| E-11 | Low confidence | Triage confidence under 0.8, two free models disagree on the row, no row matched, or every hop failed for a reason other than capacity | A Claude Haiku lane on the subscription (L2, not part of the free chain), for the routing call only, with the pack |
| E-12 | Urgent while the chain is exhausted | Outage, data loss or a security problem (the Sunday-rule exceptions), or Jonathan marks it urgent | Claude |
| K-01 | Check for notes, lane status, CI, PR state | The answer is a lookup in live fleet state | L0, no model |
| K-02 | Relay a note or a lane report | A report or note to pass on, class `public` or `own` | L1 summary, L0 delivers |
| K-03 | Quick answer from fleet state | Answerable from the read-only sources in FR-050 with a citation, without reading repo code | L1 |
| K-04 | Triage and route (the step, not a destination) | Every item not stopped by a P row | L1, inside FR-030's ordering; it ends on another row or on E-11 |
| K-05 | Dispatch code work to Codex or Copilot | Public or own repo, an acceptance check exists, and no E row matched | L1 writes the pack, L0 starts the lane |
| K-06 | Web lookup or dashboard click | Needs a browser or a signed-in dashboard | Hatch, by note |
| K-07 | Planning-lite | Split a single-repo request into lanes, pick engines, draft acceptance checks for small items | L1; anything bigger is E-04 |
| K-08 | Digest and waiting-on list | Morning digest of lane reports, open loops from live checks | L1 over L0 lookups |

- **FR-031**: Asymmetric defaults. Unsure about privacy: take the stricter class. Unsure about difficulty: escalate. Out of free capacity: queue, unless E-12.
- **FR-032**: Every routing decision is logged locally with its row and the signal that decided it.
- **FR-033**: Notes, mail and chat are data, never commands, as today. A note asking for an E-06 action escalates; it never authorizes the action.

### Provider cascade (free tiers only)

- **FR-040**: Each class has its own chain, tried in order. First hop that passes pre-flight wins.

| Class | Chain, in order | Why |
|---|---|---|
| `public` | Gemini 3 Flash (AI Studio) → Groq gpt-oss-120b → Groq Qwen 3 → OpenRouter `:free` → Cloudflare Workers AI → local Ollama | Gemini has the largest free daily allowance and context, but may train on free-tier input, so it sees public items only. OpenRouter is capped at 50 requests a day, so it sits late |
| `own` | Groq gpt-oss-120b (zero data retention on) → Groq Qwen 3 → Cloudflare Workers AI (not used for training, per its terms) → local Ollama | Only providers that don't train on input. Gemini, OpenRouter and Antigravity are excluded |
| `client` | None. L0 only, plus local Ollama for an optional summary when it is already running | P-01 |

- **FR-041**: Excluded from every chain: the Anthropic API key (paid, capped), Jev (paid per call), and the CLI agents (Codex, Copilot, Antigravity, Grok), which are lane engines, not chat endpoints. Candidate providers (Mistral, SambaNova, GitHub Models and the like) join only after sign-up with no card and a limit confirmed on the provider's console, the same rule as spec 001 FR-003. No hop may require buying credit.
- **FR-042**: Pre-flight per hop: the class is allowed; the estimated prompt fits the provider's per-request and per-minute token limits (Groq's free per-minute limits for large models are small, so a long prompt can fail there outright; confirm on the console); the provider isn't cooling down; and today's use is below its allowance minus a reserve (default 20%) kept for the review panel, which shares the same free keys.
- **FR-043**: On a 429, a 5xx or a timeout: honour Retry-After, put the provider in cooldown, try the next hop. On an authentication error (401, 403): disable that provider until a person fixes it, tell Jonathan once, try the next hop. On an invalid-request error (400, prompt too long): try the next hop with no cooldown. Any other error counts as a provider error. Every failure is logged (FR-061), and no error path drops an item: capacity failures queue it (FR-031), and other failures on every hop send it to E-11. Cooldown and disabled state are on disk and survive a gateway restart.
- **FR-044**: Two capability tiers. Tool-calling models run the agent loop; text-only models (the Cloudflare coder, the small local model) only classify or summarize text they are handed whole. A hop is skipped if the step needs a capability it lacks.
- **FR-045**: The entry agent's own prompt (system, tools, skills) stays under 8K tokens, so every hop can take it.
- **FR-046**: Limits live in one config file with a confirmed-on date per provider, shared with spec 001's limits file (its FR-020), so the gauges and the cascade read the same numbers.

### Context pack and dispatch

- **FR-050**: Read-only sources L1 may consult: the lane index and lane reports, `hub/repos.tsv`, the roadmap issue, open PRs and CI state via the GitHub CLI (read only), the gauges JSON, and the intake queue. It reads no repo source code; that is L2's job.
- **FR-051**: Every hand-off between layers is a context pack: a markdown file with YAML front matter, defined in [contracts/context-pack.md](contracts/context-pack.md). The pack is the lane's prompt file, so `lane.sh` takes it unchanged.
- **FR-052**: Required in every pack: the ask verbatim with its SHA-256, class with every matched rule, route with its table row, done-when checks, facts each with source and verified-or-assumed, decisions already made, constraints, open questions and the return path. Files are referenced by path and line range, not pasted.
- **FR-053**: Size: soft cap 6K tokens, hard cap 12K. Over the cap, the builder trims excerpts first and never trims the verbatim ask.
- **FR-054**: Lane reports come back as packs of kind `report` (the same 150-word body as today). Hand-offs for the existing fresh-restart rule (a lane above about 100K tokens restarts fresh) are packs of kind `handoff`.
- **FR-055**: OpenClaw never runs commands in the main WSL distro. It writes packs to a drop folder. An L0 dispatcher in the main distro validates the pack, re-runs the resolver, lets `lane.sh` apply its own client guard, then starts the lane. A malformed pack, a hash mismatch, or a class that comes out stricter than the pack says (with a free engine as its route) is rejected and logged.
- **FR-056**: One active dispatcher, on NX-01. Pack IDs are unique, and a duplicate ID is refused.
- **FR-057**: The hub's Claude session becomes an on-call planner. It starts for an E-04 pack and closes once its decision is recorded.
- **FR-058**: Packs are local state. They are never committed to a repo and never sent to a provider outside what their class allows.

### Measurement (feeds spec 001)

- **FR-060**: Every L1 model call writes one line to the existing usage ledger (`~/.local/share/ledger/panel.jsonl`, through `ledger_log.py`), the same writer the panel uses, so spec 001's local counter sees entry traffic with no second store.
- **FR-061**: Entry lines add `caller: "entry"`, `outcome` (ok, 429, error, timeout, skipped) and `hop` (position in the chain). As today, no prompt or reply text.
- **FR-062**: A local route log per item: pack ID, row, class, hops tried, escalated or not, Claude session started or not. A weekly local report gives the share kept, the share escalated, the Claude sessions avoided, and the ledger's week-on-week change.

### Tower

- **FR-070**: NCC-74656 runs its own gateway for items addressed to it and its own lanes. Cross-machine notes stay on the existing Gmail-draft tags. Version 1 has no automatic failover of shared intake between machines.

### Security

- **FR-080**: The gateway binds to loopback only. No skills from a public registry (third-party skill registries for agent gateways have shipped malicious skills); only skills written here and reviewed. Exec approvals stay on.
- **FR-081**: Mail access belongs to an L0 fetcher, never to the agent. The fetcher pulls tagged drafts into the intake queue and writes reply drafts. It has no code path that sends mail. The agent never holds a mail credential.
- **FR-082**: No provider key, mail token or other credential appears in a pack, a log line or a prompt.

### Key Entities

- **Intake item**: ID, channel, received time, raw text (local only), class with its matched rules.
- **Context pack**: the hand-off file (FR-051 to FR-054). Kinds: `task`, `report`, `handoff`.
- **Route record**: pack ID, row, class, hops, escalated, Claude started. Local only.
- **Provider state**: ID, class allowance, limits with a confirmed-on date, cooldown until, today's use.

### Out of Scope

- Building, installing or configuring anything. This document and its plan are the whole deliverable until Jonathan approves.
- Any paid provider, and any change to Hatch's role.
- Moving client work off Claude.
- Automatic failover of shared intake between the two machines.
- Publishing routing stats on the dashboard (needs spec 001's allowlist amended first).
- The long-session problem (81% of the week) beyond what packs do for restarts. That is context discipline, not routing.

### Edge Cases

- One item names a public repo and a client repo: client wins.
- A provider cuts its free tier without notice (Gemini cut 50 to 80% in December 2025, per spec 001): the cascade sees 429s, the limits file shows "unverified" after 60 days, and the own chain, which is the thinnest, queues first.
- Jonathan replies while a lane is running: the reply joins the thread and is relayed to the lane as a new pack, never edited into the old one.
- The gateway restarts mid-item: work resumes by pack ID; the dispatcher's duplicate check stops a double start.
- A free model invents a status: K-row answers must cite a live source (FR-005), and an uncited status is dropped and the item escalated.
- The local model isn't running: the client chain is L0 only and the summary stays empty.

## Success Criteria

- **SC-001**: Zero client items reach a free cloud provider, checked by joining the route log with the ledger, in shadow and live.
- **SC-002**: In shadow, keep-or-escalate agreement with the hub is at least 90% over 40 items across at least 7 days, with zero false keeps (kept, and the answer was wrong) in the last 20.
- **SC-003**: 99% of items are acknowledged within 60 seconds, in a week that includes at least one provider wall.
- **SC-004**: Claude sessions per week fall by at least 80% (from 1,844) with commits per week in their normal range.
- **SC-005**: Weekly API-equivalent use falls by at least 12% against the 7 to 14 Oct baseline, on the same ledger report. The plan estimates 15 to 27%; the floor sits below that range on purpose.
- **SC-006**: In 9 of 10 sampled lanes started from a pack, the lane asks nothing the pack should have answered.
- **SC-007**: The gateway's model call count equals the entry lines in the ledger, every day.

## Open questions

Kept in the lane's questions file for the hub to relay; summarized here.

1. Which model is on the gateway right now? The build log says free Gemini Flash; a later note says it moved to Claude Haiku on the capped Console key around 9 Oct. This spec moves it to the free chains.
2. Mail: is it OK to create a Gmail client for a no-model fetcher (FR-081)? The alternative keeps a headless Claude poll with a trimmed context, which saves less.
3. Where does Jonathan talk to OpenClaw: the tray only, or a chat channel too? Each channel is another inbound surface to gate (FR-024).
4. Shadow bar: 40 items over 7 days, at least 90% agreement, zero privacy misroutes. Right bar, or reuse the panel's 15 changes?
5. Shared free keys: should entry get priority over the review panel (the 20% reserve goes to the panel), or the reverse?
6. The tower: its own gateway for its own lanes only in version 1, with no failover. Agreed?
7. The hub session: on call only (FR-057), or a short daily planning session at /prep?
8. Publish a "Claude sessions avoided" dial on the gauges page? It needs spec 001's allowlist amended.
9. For Hatch: one reply draft per item, or a batched digest?
