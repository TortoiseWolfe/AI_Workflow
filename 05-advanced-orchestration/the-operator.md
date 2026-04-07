# The Operator Terminal

The Operator is the meta-orchestrator. It runs **OUTSIDE** the tmux session, managing the 27 worker terminals **INSIDE** it. The Operator is your proxy — when you're not at the keyboard, the Operator keeps the system productive by dispatching work, monitoring progress, and escalating blockers.

This page is the most important in Chapter 05. If you understand the Operator, the rest of the assembly line clicks into place.

---

## Mental model

```
┌─────────────────────────────────────────────────────────────┐
│  YOUR TERMINAL (outside tmux)                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  OPERATOR (you, or a Claude Code session you started) │  │
│  │  - Launches: ./scripts/tmux-session.sh --all          │  │
│  │  - Dispatches: ./scripts/tmux-dispatch.sh             │  │
│  │  - Monitors: tmux capture-pane                        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ manages via `tmux send-keys ... Enter`
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  TMUX SESSION "scripthammer" (27 windows)                   │
│  Windows named by ROLE, not number                          │
│  Each window is its own Claude Code session                 │
└─────────────────────────────────────────────────────────────┘
```

The Operator never *does* work itself. It only **dispatches**, **monitors**, and **escalates**. Workers do the work.

---

## CRITICAL: tmux send-keys requires Enter

This single lesson took TurtleWolfe a week to fully internalize. Do not skip it.

**Commands sent to tmux are NOT executed until you send Enter separately.**

```bash
# WRONG — command is queued but never submitted
tmux send-keys -t scripthammer:RoleName "/clear"
tmux send-keys -t scripthammer:RoleName "/prime developer"

# CORRECT — Enter actually executes the command
tmux send-keys -t scripthammer:RoleName "/clear" Enter
sleep 3
tmux send-keys -t scripthammer:RoleName "/prime developer" Enter
```

This applies to **every** command: `/clear`, `/exit`, `/prime`, prompts, everything. If you forget the `Enter`, the command sits in the worker's input buffer doing nothing.

**Symptom of forgetting Enter:** The Operator thinks it dispatched work; the worker is still idle. You'll see this in `tmux capture-pane` — the command is visible at the cursor but not yet submitted.

---

## CRITICAL: Name-based dispatch (NO window numbers)

Window numbers in tmux are **fragile**. They change based on which terminals you started, in what order, and whether any have been killed and recreated. **Always dispatch by role name, never by window number.**

```bash
# WRONG — window number can change
tmux send-keys -t scripthammer:5 "..." Enter

# CORRECT — name is stable
tmux send-keys -t scripthammer:Toolsmith "..." Enter
```

To find a worker by name:
```bash
tmux list-windows -t scripthammer -F "#{window_index}:#{window_name}" | grep Toolsmith
```

To capture the current state of a worker:
```bash
tmux capture-pane -t scripthammer:Developer -p | tail -30
```

---

## Lifecycle commands

These are the operator's bread and butter. Memorize them.

```bash
# 1. Launch workers (creates the tmux session with all 27 windows)
./scripts/tmux-session.sh --all
# Then Ctrl+b d to detach and return to your shell

# 2. Check status across all workers
./scripts/tmux-dispatch.sh --status

# 3. Dispatch work
./scripts/tmux-dispatch.sh --vote    # Send pending RFC votes to council
./scripts/tmux-dispatch.sh --tasks   # Send audit items to owners
./scripts/tmux-dispatch.sh --queue   # Process the wireframe queue
./scripts/tmux-dispatch.sh --all     # Everything at once

# 4. Monitor a specific worker BY NAME
tmux capture-pane -t scripthammer:Toolsmith -p | tail -30

# 5. Find stuck workers (waiting on permission)
for win in $(tmux list-windows -t scripthammer -F "#{window_name}"); do
  if tmux capture-pane -t scripthammer:$win -p | grep -q "Do you want to proceed"; then
    echo "$win stuck on permission prompt"
  fi
done

# 6. Check completion (count completed audits)
grep -c '✅' docs/interoffice/audits/*.md

# 7. Attach to observe interactively (Ctrl+b d to detach)
tmux attach -t scripthammer

# 8. Kill the session when done
tmux kill-session -t scripthammer
```

---

## The Operator's responsibilities

1. **Launch** the tmux session with appropriate workers
2. **Dispatch** work using the dispatcher scripts
3. **Monitor** progress across all terminals
4. **Re-dispatch** to stuck or idle terminals
5. **Escalate** blockers to the human user
6. **Report** status summaries to the human user
7. **Keep the system productive** — no idle terminals when there's work in the queue

The Operator does NOT:
- Write code
- Make architectural decisions
- Vote on RFCs
- Run tests
- Generate wireframes
- Touch any files itself (other than reading and dispatching)

If you find your Operator doing any of those, you've blurred the layers. The Operator is a switchboard, not a worker.

---

## Priming the Operator

The Operator has its own primer file. When you start the Operator terminal, run:

```
/prime operator
```

This loads:
- `CLAUDE.md` (project context)
- `.claude/roles/operator.md` (operator role definition)
- Whatever inventory files the operator role needs

If you have a custom `prep-operator.md` per project (TurtleWolfe does, for ScriptHammer and TurtleWolfe), use that instead — it includes the lifecycle commands and the lessons-learned section.

---

## Lessons learned

These are scars from running the assembly line. Read them.

1. **Never use shortcodes or assumed role names.** If you're not sure of a role's exact name, check `scripts/tmux-session.sh` for the `ALL` array.

2. **Always send Enter after `tmux send-keys`.** Always. Always. Always.

3. **Use name-based dispatch (`:RoleName`), never window numbers (`:5`).** Window numbers will betray you.

4. **Do exactly what you're told — nothing more, nothing less.** When the user says "shut down 10 terminals," shut down those 10. Don't kill the whole session because it seems "cleaner." Don't keep extras alive because they "might be needed." Match the scope of your action to the request.

5. **When in doubt, ask.** The Operator's job is to escalate blockers. If you don't know whether to do something, escalate. Don't guess.

6. **Idle terminals are a signal.** If a worker is idle and the queue isn't empty, you have a routing bug. If the queue is empty and workers are idle, you have a planning gap. Either way, take action.

---

## Anti-patterns

| Anti-pattern | Why it's wrong |
|---|---|
| Operator runs `/code-review` | Operator dispatches `/code-review` to a worker. Operator doesn't do work itself. |
| Operator decides architecture | Architect decides architecture. Operator dispatches to Architect. |
| Operator writes commits | Developer writes code, commits via `/commit`. Operator coordinates. |
| Operator forgets Enter and times out waiting | Read this page again. |
| Operator hardcodes window numbers | Use names. The session reorders windows constantly. |
| Operator kills the whole session because one worker is stuck | Kill the stuck worker, restart it, dispatch it. Don't nuke the session. |

---

## Related

- [README.md](README.md) — chapter overview
- [the-assembly-line.md](the-assembly-line.md) — what the operator dispatches to
- [roles.md](roles.md) — every worker the operator manages
- [dispatch-and-queue.md](dispatch-and-queue.md) — the queue protocol
- [`~/repos/Claude_Commandz/repos/ScriptHammer/.claude/commands/prep-operator.md`](https://github.com/TurtleWolfe/Claude_Commandz) — the real `prep-operator` command from production
