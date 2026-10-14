# Feature Specification: Fleet Gauges (steampunk free-tier dashboard)

**Feature Branch**: `gauges-spec`
**Created**: 2026-10-12
**Status**: Draft (spec only: no build, no signups, no keys). The six open questions were decided by Jonathan on 14 Oct 2026; see Decisions at the end.
**Input**: A dashboard of brass gauges, like 1945 car dials or an old cockpit, one gauge per LLM in the fleet, showing how much of its **free tier** the fleet actually uses. Free tiers only; nothing paid is ever wired in. Static GitHub Pages site in this repo, refreshed every 6 to 12 hours by a local collector, publishing aggregate numbers only.

Research behind the data-source choices: 18 providers surveyed 2026-10-12. Most limits below are third-party figures and are marked so; each must be checked against the provider's own console before its gauge is calibrated.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - See the fleet's free-tier burn at a glance (Priority: P0)

As a visitor (an intern, a viewer, a client), I open one page and see a row of dials, one per free-tier LLM, so I can tell in five seconds which providers the fleet is leaning on.

**Why this priority**: The dashboard is the whole feature. Without a readable, honest page nothing else matters.

**Independent Test**: Open the page from a static file server with a fixture data file. Every gauge renders, shows a needle, a label and a "last updated" time, with no network calls beyond the page's own files.

**Acceptance Scenarios**:

1. **Given** a data file with 7 providers, **When** the page loads, **Then** 7 gauges render, each with provider name, percent of free allowance used and the window it covers (day, month)
4. **Given** a provider that is unclaimed (no account yet) or idle (no calls for the idle threshold), **When** the page loads, **Then** its dial is still drawn but dimmed, lamp off, needle at rest, labelled "not claimed" or "idle since <date>", never hidden
2. **Given** a gauge whose data is older than 2x the refresh interval, **When** the page loads, **Then** that gauge shows a "stale" state (needle greyed, age shown), not its last value as if current
3. **Given** a provider with no calibrated limit, **When** the page loads, **Then** its gauge shows "uncalibrated" and a raw call count, never an invented percentage

---

### User Story 2 - Trust the numbers (Priority: P0)

As Jonathan, I need every gauge to be proven against the provider's own number before it is shown as calibrated, so the dashboard is never decoration.

**Why this priority**: Accuracy first. A pretty gauge that is wrong is worse than none.

**Independent Test**: For each provider, compare the collector's count for one full window with the provider's console figure; record both in the calibration log. Within the tolerance in FR-009, the gauge is marked calibrated.

**Acceptance Scenarios**:

1. **Given** a provider whose own endpoint reports usage (OpenRouter), **When** the collector runs, **Then** the gauge uses the provider's figure and the local count is kept only as a cross-check
2. **Given** a provider with no readable endpoint, **When** its local count differs from the console beyond tolerance, **Then** the gauge stays "uncalibrated" and the difference is logged
3. **Given** a provider whose published limits conflict between sources (Groq: 1,000 vs 14,400 requests/day), **When** configured, **Then** the limit comes from the provider's console and the source is recorded in the config

---

### User Story 3 - Nothing private ever publishes (Priority: P0)

As Jonathan, I need the published data to contain aggregate numbers only, so a keys leak or a client leak is impossible by construction.

**Why this priority**: The site is public. One leaked key or client string is a rotation-and-history-rewrite incident.

**Independent Test**: Feed the publisher a fixture containing a fake key, a client repo name, an email and a prompt string; the publish step refuses and nothing is written to the Pages branch.

**Acceptance Scenarios**:

1. **Given** the collector output, **When** the publisher builds the public file, **Then** only fields in the allowlist (FR-011) are present; any other field fails the build
2. **Given** the public file, **When** the privacy gate runs on the commit diff (FR-013), **Then** any secret finding stops the publish and nothing is pushed
3. **Given** a repo on the client list, **When** calls are counted, **Then** they land in the same aggregate counter as every other call, with no per-repo breakdown anywhere

---

### User Story 4 - Keep the gauges alive without babysitting (Priority: P1)

As Jonathan, I need the collector to run every 6 to 12 hours and publish by itself, and to say so loudly when it stops.

**Why this priority**: A dashboard that silently freezes is the usual way these die.

**Independent Test**: Stop the collector for two intervals; the page shows every gauge stale and a banner "collector silent since <time>".

**Acceptance Scenarios**:

1. **Given** the schedule fires, **When** collection and the gate succeed, **Then** a commit lands on the publishing branch and Pages rebuilds
2. **Given** the gate or a provider call fails, **When** the run ends, **Then** the previous published file stays, the failure is logged locally and the page's age display keeps counting up
3. **Given** a provider is down, **When** the run happens, **Then** only that gauge goes stale; the others update

---

### User Story 5 - Reuse the dials elsewhere (Priority: P2, later phases)

As the channel owner, I want the same data to feed a Twitch offline panel, a small periodic on-air overlay, and a link from the head-chef-line-cooks blog post.

**Why this priority**: Nice reach, but each is a consumer of the published file and none changes the core.

**Independent Test**: Each consumer reads only the public JSON file; none needs a new data path.

**Acceptance Scenarios**:

1. **Given** the public JSON, **When** a Twitch panel image is generated, **Then** it is a static render of the same numbers, regenerated per publish
2. **Given** the overlay, **When** it shows, **Then** it is a browser source in the streaming software reading the public Pages file, never the collector's local store, and it shows pacing plus a generic label only (FR-028)
3. **Given** the blog post, **When** updated, **Then** it links the dashboard URL and adds no numbers of its own

## Requirements _(mandatory)_

### Functional Requirements

**Gauges and providers**

- **FR-001**: One dial per free-tier provider, whether or not the fleet uses it yet. Day one (decided 14 Oct): the six in the fleet today (Gemini (AI Studio), Groq, Cloudflare Workers AI, OpenRouter (`:free` models), Antigravity CLI, local Ollama) plus the three free tiers not yet claimed (Mistral Experiment, SambaNova Cloud, GitHub Models), which start dimmed as "not claimed". A dial that is not pulling its weight stays on the board; that is the point.
- **FR-002**: Free tiers only. A provider with no free tier (Jev, Anthropic API, Together, DeepSeek, Grok) never gets a gauge. Adding a card-requiring provider is out of scope by rule, not by default.
- **FR-003**: A dial for Mistral Experiment, SambaNova Cloud and GitHub Models exists from day one but stays "not claimed" (dimmed, raw count only, no percent) until the owner signs up and a limit is confirmed on the provider's console, at which point it is switched on. Further candidates, not in the 14 Oct decision and added the same way: Cohere trial, NVIDIA NIM; Cerebras only if signup asks for no card.
- **FR-004**: Each gauge shows percent of the free allowance used in its current window, the window (daily, monthly, weekly), the reset time where the provider gives one, and a state: calibrated, uncalibrated, stale, idle or unclaimed. Idle (claimed, but no calls for the idle threshold) and unclaimed (no account yet) both dim the dial, lamp off, so dead water is visible; stale means the data is old, not that the provider is unused.
- **FR-005**: Local Ollama has no allowance. Its dial is a load meter (GPU busy, requests per hour) and is labelled "local, unlimited" so it is never read as a quota.
- **FR-006**: Antigravity publishes no numbers (weekly quota of "work done"). Its gauge is permanently "uncalibrated" unless the vendor publishes a limit; it shows a raw count and a note.

**Data sources per gauge** (all third-party limits are to be confirmed on the console)

| Gauge | Window | Used figure comes from | Limit comes from |
|---|---|---|---|
| OpenRouter free | daily | Provider's key endpoint (used, limit, remaining for free models); local count as cross-check | The endpoint (50 requests/day without purchased credit; do not buy credit) |
| Groq | daily | Local call counter; response headers on the last call as cross-check | Console (published figures conflict) |
| Cloudflare Workers AI | daily, resets 00:00 UTC | Local counter converted to Neurons; the provider's analytics API if it can be read read-only | 10,000 Neurons/day (official) |
| Gemini (AI Studio) | daily | Local counter | Console; roughly 1,000-1,500 requests/day on Flash (third-party, changes often) |
| Antigravity CLI | weekly | Local counter of invocations | None published |
| Ollama (local) | rolling hour | Local server state and GPU stats | None (load meter) |
| Mistral, SambaNova, GitHub Models (FR-003, dimmed until claimed) and later candidates | per provider | Local counter once claimed | Console; for example Cohere 1,000 calls/month (official) |

- **FR-007**: Only OpenRouter has a readable usage endpoint today; Groq exposes per-request headers. Every other gauge depends on a **local call counter** placed in front of the provider, the one uniform design. The counter logs a timestamp, provider and token counts only.
- **FR-008**: The counter reuses the existing usage ledger the review panel already writes (one line per call) rather than a second store. Calls made outside the ledger (a tool talking to a provider directly) are counted by adding the ledger line, not by scraping. Both machines (NX-01 and the tower) keep a ledger; see FR-017.
- **FR-009**: Calibration rule: a gauge is "calibrated" only after one full window where the local count is within 5% (or 2 calls, whichever is larger) of the provider's own figure. The comparison and date go in a calibration log kept locally. Failing it is a finding, not a reason to loosen the tolerance.

**Publishing and privacy**

- **FR-010**: Output is one static JSON file plus the page's HTML, CSS and SVG, served by GitHub Pages from this repo. No server code, no client-side calls to any provider.
- **FR-011**: Allowlist schema, enforced by the publisher (unknown fields fail the build): `generated_at`, `activity` (one of: idle, working; fleet-wide, see FR-028), per provider `as_of` (when that provider's figure was last read, so one provider can go stale alone), `id`, `display_name`, `window`, `weight` (one of: small, medium, large; dial size, see FR-026), `used`, `limit` (or null), `unit`, `percent` (or null), `state` (one of: calibrated, uncalibrated, stale, idle, unclaimed), `resets_at`, `source` (one of: provider, local-count). Nothing else.
- **FR-012**: Never published: keys, tokens, auth headers, prompts, replies, repo names, file paths, branch names, client names, per-task or per-repo breakdowns, account identifiers, email addresses, the machine name.
- **FR-013**: The publisher runs the review panel's privacy gate (`panel_gate.py`) on the diff of the file it is about to commit, with class `public`, and reuses its rules rather than copying them: secret scan first and fails closed (no scan result means no publish), redaction counts above the maximum stop the run, a `never_send` list blocks any path outside the dashboard files. Any finding aborts before commit.
- **FR-014**: The pre-push hook and gitleaks run on the publishing branch like any other push. A hook failure stops the run and is reported, never bypassed.
- **FR-015**: Counts are aggregate over all repos, client and personal alike. Client repos are not distinguished; the dashboard does not reveal whether a repo exists.
- **FR-016**: Provider API keys stay where they already live (outside every repo). The collector reads usage from local logs and, for OpenRouter, makes one authenticated read per run; no key value is printed, logged or placed on a command line.

**Refresh**

- **FR-017**: A local collector runs every 6 to 12 hours (default 8; Hatch's note allows 6 to 12 and the number is not a Jonathan decision). Both machines' ledgers are merged from day one (decided 14 Oct): the tower sends its ledger lines (timestamp, provider, token counts only, FR-007) to the publishing machine, which merges them, builds the file, runs the gate, commits and pushes. A gauge is not marked calibrated until the merge covers every machine that makes calls to that provider. Before building the sync, the build checks which free-tier calls the tower makes today.
- **FR-017a**: Data commits go to `main` (decided 14 Oct; Pages is served from `main`, path `/`). One data file, one commit per run, and no push when the figures have not changed since the last published file. CI and the tidy report ignore the data file's path so the commits do not trigger builds or noise. The publish step still passes the gate (FR-013) and the pre-push hook (FR-014) like any other push.
- **FR-018**: A gauge whose `as_of` is older than 2x the interval shows stale; the page shows a banner when every gauge is stale.
- **FR-019**: The page shows the generation time and its age, computed in the browser from `generated_at`.
- **FR-020**: Free-tier limits drift (Gemini was cut 50-80% in December 2025). Limits live in one config file with a "confirmed on" date per provider; a limit not confirmed in 60 days shows a small "limit unverified" mark.

**Look and accessibility**

- **FR-021**: Steampunk dial styling: brass bezel, aged face, riveted plate, needle with an easing sweep, small-caps engraved labels, in the mood of a 1945 dash or a cockpit panel. Pure SVG and CSS, no image dependencies.
- **FR-022**: The dial is decoration over data: each gauge also has its number as text ("62% of daily allowance, 31 of 50 requests"). Colour is never the only signal; red zones also have a pattern or label.
- **FR-023**: WCAG AA contrast on the text layer, reduced-motion support (needle jumps instead of sweeping), keyboard-readable order, and a plain table view toggle. The page passes Pa11y.
- **FR-024**: Follows this repo's two-layer style (plain line with an analogy, technical detail beneath) in the explainer text, with sections collapsed by default.
- **FR-025**: The page is a top-level page beside `series.html` (decided 14 Oct), linked from chapter 05 and from the head-chef-line-cooks post. Chapters 00-04 do not depend on it.
- **FR-026**: Dial size scales with the work the provider is expected to carry (decided 14 Oct): each provider has a `weight` (small, medium, large) in the config, set by the owner. A small dial for a provider expected to carry little is not a defect, but a large dial that sits dim is the signal the board exists to give.
- **FR-027**: The unclaimed and idle states (FR-004) render as a dimmed dial with the lamp out and the needle at rest, never as a hidden dial and never as a 0% that looks like a measurement. The idle threshold is a config value (proposed default 7 days, to be confirmed).
- **FR-028**: Overlay data contract (later phase): the on-air overlay shows pacing against the free allowances plus a generic activity label chosen from a fixed set ("a build lane is running" or "idle") derived from recent ledger activity. It never shows a repo, task, client or branch name; FR-012 holds. The overlay is an OBS browser source reading the public data file on the Pages site.

### Key Entities

- **Provider**: id, display name, window, limit, limit source, confirmed-on date, free-tier-only flag.
- **Usage sample**: provider id, timestamp, units (requests or Neurons or tokens). Local only; never published.
- **Published snapshot**: the allowlisted JSON (FR-011), one file, overwritten each run.
- **Calibration record**: provider, window, local count, provider figure, difference, date. Local only.

### Out of Scope

- Anything paid: Jev, Anthropic API, Codex or Copilot subscriptions, OpenAI data-sharing credits, Grok. No gauge, no spend tracking.
- Signing up for any provider, creating keys, or touching billing (the owner does these one step at a time).
- Cost, latency, quality or per-model leaderboards.
- Any per-repo, per-client, per-task or per-person breakdown.
- Alerts, throttling or automatic routing that reacts to the gauges (a possible later feature, not this one).
- The build itself: this document is the spec; plan, tasks and code come after Jonathan elaborates.
- Twitch panel, overlay and blog edit are later phases (User Story 5); only their data contract (the public JSON and FR-028) is fixed here.

### Edge Cases

- A provider changes its limit mid-window: percent can briefly exceed 100; show it capped at the dial's end with the true number in text.
- Two machines both call the same provider: both ledgers are merged (FR-017). If a machine's ledger is missing from a run, that provider's gauge is "uncalibrated" for the run rather than undercounting.
- No push when nothing changed (FR-017a) must not look like a dead collector: the page's age comes from `generated_at` and `as_of` (FR-018, FR-019). The collector therefore still publishes at least once a day (proposed, to be confirmed) so a quiet board does not turn stale.
- Clock and reset differences: Cloudflare resets 00:00 UTC; others roll per account. The window label states which.
- A provider is disabled or removed from the fleet: its gauge is retired from the config, not left at zero.
- Collector runs while the ledger is being written: read a consistent snapshot; never publish a half-written file (write temp, then rename).

## Success Criteria

- **SC-001**: A first-time visitor can name the most-used provider in under 10 seconds.
- **SC-002**: Every gauge marked calibrated has a calibration record within the FR-009 tolerance.
- **SC-003**: The published file contains only allowlisted fields, verified by a test that fails on any extra field.
- **SC-004**: Zero secret findings across the gate, gitleaks and the pre-push hook on every published commit.
- **SC-005**: The page is never more than 2x the refresh interval stale without saying so.
- **SC-006**: Page weight under 300 KB and no runtime requests to any third party.

## Decisions (Jonathan, 14 Oct 2026)

All six questions are decided. The answers came as question dialogs in the hub; the quote in item 1 is his own words.

1. **Day-one providers: all of them.** "put all of them on the dashboard, if they aren't pulling their weight that's the point we'll have a visual que to get them active and nudge their progress, you can size them appropriately if they aren't expected to pull much weight, but if they are dead water we need to see that, maybe the lights dimmed out until they are powered on?" Touches FR-001, FR-003, FR-004, FR-011, FR-026, FR-027, User Story 1. Grok, OpenAI and Jev stay off under FR-002.
2. **Antigravity: a dial, permanently uncalibrated.** Settled by decision 1; raw count plus a note, no guessed limit (FR-006, unchanged).
3. **Collector: both machines now, ledgers merged from day one.** FR-008, FR-017 and the two-machine edge case.
4. **Data commits: on `main`.** One data file, one commit per run, no push when nothing changed, CI and the tidy report ignore the path. FR-017a.
5. **Page: top level, beside `series.html`**, linked from chapter 05 and the head-chef-line-cooks post. FR-025.
6. **Overlay (later phase): pacing plus a generic label, via an OBS browser source** reading the public data file; never repo, task or client names. FR-028, User Story 5.

## Still open (left by the decisions)

- **Tower sync path.** How the tower's ledger lines reach the publishing machine (FR-017), and the first check of what free-tier calls the tower makes today. A build-lane design question; it must carry the same aggregate-only fields (FR-007).
- **Idle threshold.** Proposed 7 days with zero calls before a claimed dial dims (FR-027).
- **Dial weights.** The small, medium or large setting for each of the nine providers (FR-026) is for the owner to set; no value is assumed here.
- **Quiet-board heartbeat.** "No push when nothing changed" against the staleness rule needs at least one publish a day (proposed, edge cases).
- **Overlay wording.** The exact fixed set of generic labels (FR-028).
