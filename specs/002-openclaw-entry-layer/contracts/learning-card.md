# Contract: Learning card, metrics and change log, version 1

The learning loop's three artifacts. Spec: [../spec.md](../spec.md), User Story 7 and FR-090 to FR-099.

- **Card**: one proposed change, filed as a GitHub issue in the private `TortoiseWolfe/workspace` repo. Jonathan approves or rejects it on the issue.
- **Metrics**: the five numbers the loop is allowed to move, each with a fixed source.
- **Change log**: everything that could move a metric, so an effect is never credited to the wrong change.

## Metrics

Windows run from Wednesday 12:00 ET to Wednesday 12:00 ET, the subscription's weekly reset. Per-lane figures stay local, as spec 001's FR-012 requires; a card carries engine-level or fleet-level figures only.

| ID | Metric | Unit per window | Source | Better | Guard metrics |
|---|---|---|---|---|---|
| M1 | Context load | Tokens per turn (median, p90) and turns over 200K | Spec 001's context-load readings (its FR-029, FR-030): per main-thread turn, input plus cache writes plus cache reads, from the usage ledger | Lower | M3; SC-002 |
| M2 | Compactions | Count, auto versus manual, per 100 turns | `compact_boundary` entries in session transcripts (spec 001 FR-030) | Lower, read together with M1 | M1. Fewer compactions bought by letting contexts grow larger is not a win, because Jonathan set the compaction window for accuracy |
| M3 | Director first-pass review rate | Share of reviewed items the blind reviewer passed on the first review, by worker tier | `hub/scripts/model_quality_report.py --json`, section C (director run logs) | Higher | M1 |
| M4 | Free-tier share of model calls | Free-tier calls divided by all model calls (free tiers, Claude main-thread turns, Codex and Copilot calls); one call counts once whatever its size, since M1 covers size | Entry and panel lines in the usage ledger (spec FR-060, FR-061) plus the ledger's Claude rows | Higher | M5; SC-001; SC-002 |
| M5 | Avoidable escalations | Count, and share of all escalations | The route log (FR-062): escalated items whose lane changed no file, opened no PR and ran under 10 turns. Each one is re-run on the free chain in shadow, and the card shows both answers side by side | Lower | SC-001; SC-002 |

**Noise band**: the largest week-to-week change within the baseline windows (at least two, up to four), and never less than 10%. A move inside the band is "no effect", never "a small win".

**Existing rules are not overridden**: M3 already has a rule in the quality report (a worker tier under 85% first-pass review gets bumped up a tier). The loop can propose changing that rule, but only through a card, like any other change.

## Card

**Title**: `[learning] M<n>: <the change in a few words>`

**Labels**: `learning-proposal` is always on. Exactly one state label is added:
- `approved`, set by Jonathan's own account only
- `measuring`
- `kept`
- `reverted`
- `confounded`
- `rejected`

**Body template**:

```markdown
<!-- learning-card v1 -->
**Card**: L-2026-11-04-01 · **Metric**: M1 · **Guards**: M3, SC-002
**Built by**: entry-l1 · **Models used**: groq/openai/gpt-oss-120b

## Change
One sentence. Files or settings touched: <path or setting>. Applied by: a lane on <engine>.

## Why
- <claim> · source: <path:line, command and date, or URL> · verified | assumed

## Baseline
| Window (Wed 12:00 ET) | Value | Source |
|---|---|---|
| <start> to <end> | <number> | <command and date> |
| <start> to <end> | <number> | <command and date> |
Noise band: <number> (largest week-to-week swing above; at least 10%).

## Prediction
Direction and size, for example "median tokens per turn down 10 to 20%".

## Revert path
Exactly how to undo it, step by step. Approving the card approves this too.

## Confounders known now
Change-log entries that overlap the planned window, or "none".

## The loop's record
Last 10 cards: applied N, kept N, reverted N, confounded N. Median prediction error: N%.

## Result (filled in after the window)
Measured: <number> · source: <command and date> · verdict: keep | revert | confounded
Re-checks (FR-099): week 1 <number>, week 2 <number>, ...
```

**Validation** (L0, before the issue is filed; a refused card is logged locally and never filed):

1. Exactly one target metric, and that metric has no card in the `measuring` state.
2. At least two baseline windows, each with a source.
3. Every number in Why, Baseline and Prediction has a source (or, for the prediction, is marked as a prediction).
4. The revert path is not empty.
5. The privacy gate returns `send` at class `own`, with no client term found. Client-derived inputs appear as counts only.
6. Fewer than three cards are open.

## Change log

A local JSON Lines file (one entry per line), for example `~/.claude/state/learning/changes.jsonl`. It is never published.

```json
{"ts": "2026-11-05T03:00:12-05:00", "kind": "dreaming", "ref": "run-2026-11-05", "machine": "NCC-74656", "metrics": ["M4", "M5"], "noop": false, "before": "sha256:...", "after": "sha256:..."}
```

| Field | Meaning |
|---|---|
| `kind` | `card-apply`, `card-revert`, `rollout-phase`, `dreaming`, `watched-commit`, `model-change` or `provider-limit` |
| `ref` | The card ID, commit SHA, phase name or run ID |
| `metrics` | The metrics this change can move. The writer fills it in from a fixed map: watched `CLAUDE.md` files and hooks touch M1 to M3, routing rules touch M4 and M5, and dreaming touches M4 and M5 |
| `noop` | Dreaming only. True when the agent's memory and skills hash the same before and after, in which case the run confounds nothing |

Watched commits are found by L0 reading the git log of the watched paths in FR-098. Nothing depends on anyone remembering to log a change.
