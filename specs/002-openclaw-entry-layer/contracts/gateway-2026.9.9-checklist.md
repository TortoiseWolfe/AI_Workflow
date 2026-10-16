# Gateway feature checklist: OpenClaw 2026.9.9

Phase 0 of [plan.md](../plan.md). Checked 16 Oct 2026 on NX-01 (gateway distro, version 2026.9.9, commit bcfc888).
Each row cites the bundled documentation of the installed build (path under the package's `docs/`; the same page
is at `https://docs.openclaw.ai/<path without .md>`) and says what was run, not only what the page claims.

| # | Needed by | Feature | Status | Source and evidence |
|---|---|---|---|---|
| 1 | FR-040 | Ordered model fallbacks | **Works.** Applied and read back: default `google/gemini-3-flash-preview`, fallback `claude/claude-haiku-5-5`. A one-shot call through the gateway answered from Gemini. The fallback hop itself was not forced to fire (Phase 2 fault injection does that). | `concepts/model-failover.md` ("Model fallback to the next model in `agents.defaults.model.fallbacks`"); `openclaw models status`; `openclaw infer model run --gateway` |
| 2 | FR-040 | A different chain per privacy class | **Possible, not set up.** A native agent's own `model.fallbacks` replaces the shared list, and an agent without one is strict. So one agent per class, each with its own chain, is the supported shape. The `before_model_resolve` hook can also switch model per turn. | `concepts/model-failover.md` ("Selection source policy"); `plugins/hooks/prompt-and-session.md` |
| 3 | FR-024 | A deterministic step before the model on each channel | **Available as a plugin hook, untested here.** `before_dispatch` is a "claim" hook that handles an inbound message before normal model dispatch. It needs a local plugin. Whether the tray's channel runs it is not shown in the docs, and is a Phase 2 test. Version 1 has the tray as its only channel (question 3). | `plugins/hooks/reference.md` (hook table); `plugins/hooks/messages.md` |
| 4 | FR-080 | Loopback-only bind | **Works.** `gateway.bind` defaults to `loopback`; gateway auth is required on any other bind. Listening on 127.0.0.1:18789 was checked on 15 Oct. | `gateway/config-gateway.md` ("bind", "Auth") |
| 5 | FR-080 | Local-only skills | **Possible, to be pinned in Phase 2.** Skills load from workspace, managed and bundled tiers, and `skills.allowBundled` plus per-agent `skills` allowlists restrict what an agent sees. ClawHub is an optional source. Pinning the entry agent to its four local skills is a Phase 2 step. | `tools/skills.md` (precedence); `tools/skills-config.md` ("Bundled skill allowlist", "Agent allowlists") |
| 6 | FR-081, FR-082 | Credentials held as SecretRefs | **Partly in use.** The `claude` provider is already `secretref-managed`. The Google key sits in the auth store as a plain API-key profile. SecretRefs are opt-in per credential, and plaintext in files the agent can read stays agent-readable. | `gateway/secrets.md`; `openclaw models status` |
| 7 | FR-080 | Exec approvals stay on | **Does not hold as written.** The gateway's exec is set to full, with no prompts, and the docs say a gateway full-session can skip host approval evaluation. The gateway distro has no mount of the main distro and no interop, so the reach is that distro only. FR-080 should say "the distro's isolation, not exec approvals, is the boundary", or the setting should be tightened in Phase 2. | `tools/exec-approvals.md` (opening notes) |
| 8 | FR-055 | A path between the gateway distro and the main distro | **Works: `/mnt/wsl`.** Same tmpfs in both distros, mode 1777. A file written by `openclaw` in one distro was read by `TurtleWolfe` in the other, and the reverse. See the finding below. | Test run 16 Oct: `findmnt` shows tmpfs; two-way write and read |
| 9 | FR-060 | Model call counts for the ledger | **Not tested.** The ledger writer is the main distro's; Phase 2 decides whether the gateway's logs or a hook feed it. | `gateway/protocol/ledgers.md` names a gateway ledger; not read further |

## Findings that change the plan

1. **The drop folder works, so the Debian service is not needed.** `/mnt/wsl/<folder>` is writable from both sides.
   Three limits: it is a tmpfs, so it empties when WSL itself shuts down (the dispatcher recreates it at start, and
   packs in flight are re-sent by pack ID, FR-055); both users are uid 1000, so file permissions do not separate
   the gateway from the main user (the dispatcher's validation is the only guard, as the plan already says); and
   every distro can read it, so packs must never hold a credential (FR-082).
2. **FR-080's "exec approvals stay on" needs rewording** (row 7).
3. **`openclaw models status` prints a masked fragment of the Google API key** on its auth line. A lane that
   reads that output must mask it first. Not a leak to the network, but a fragment of a credential in a log.
4. **`models status --probe` refuses to run while the gateway is up.** Use `openclaw infer model run --gateway`
   for a live one-token check.
5. **Rollback is tested.** The pre-upgrade archive extracts to a staging folder and its own binary reports
   2026.9.6; the model chain rolls back and forward with `models set` and `models fallbacks clear` / `add`.
