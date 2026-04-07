# Chapter 00 — Start Here

**Day-1 question:** *"Is my setup even working?"*
**Time budget:** 15 minutes
**You'll finish with:** A confirmed working Claude Code install, a four-line `settings.json`, and your first successful `/help`.

---

## The 3-step smoke test

1. Open a terminal and run:
   ```bash
   claude --version
   ```
   You should see a version string. If you see "command not found", you don't have Claude Code installed — see [install-claude-code.md](install-claude-code.md).

2. Run `claude` in any directory. At the prompt, type `/help` and press Enter. You should see a list of built-in commands. If `/help` works, your install is fine.

3. Read [first-conversation.md](first-conversation.md) — a 5-minute primer on reading Claude's output, when to interrupt, and the three buttons you need to care about.

That's it. You're ready for [Chapter 01](../01-bootstrap-a-repo/).

---

## Dig deeper

### The four-line `settings.json`

TurtleWolfe's global Claude Code settings live at `~/.claude/settings.json` and are exactly four meaningful lines:

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.claude/statusline-command.sh"
  },
  "alwaysThinkingEnabled": true,
  "model": "opus"
}
```

**Why these four:**

| Setting | Why |
|---|---|
| `statusLine` | Custom status line script — shows project, branch, and model in the prompt. Optional. |
| `alwaysThinkingEnabled: true` | Claude thinks before every response. For real work this is almost always the right call — the small latency cost is dwarfed by the quality improvement. |
| `model: opus` | Opus is the default. Override per-session with `/fast` for Haiku or `/model sonnet` mid-conversation. |

You don't need a status line script on Day 1. Start with just the last two lines:

```json
{
  "alwaysThinkingEnabled": true,
  "model": "opus"
}
```

### What lives in `~/.claude/`?

| Path | What |
|---|---|
| `~/.claude/settings.json` | Global settings (the four lines above) |
| `~/.claude/commands/*.md` | Global slash commands available in every repo |
| `~/.claude/statusline-command.sh` | Optional status line script |
| `~/.claude/plans/*.md` | Plans from plan mode (auto-generated, safe to delete) |
| `~/.claude/projects/*/memory/*.md` | Persistent memory per project |

You'll add files to `~/.claude/commands/` in [Chapter 03](../03-slash-commands/). For now, leave it alone.

### What NOT to configure on Day 1

Resist the urge to configure hooks, MCP servers, custom agents, or output styles. You don't need them yet. Get through Chapter 01 with the four-line settings and come back to advanced config when a specific need arises.

---

## If something broke

- `claude --version` fails → Claude Code isn't installed. See [install-claude-code.md](install-claude-code.md).
- `/help` shows nothing → Your install is partial. Uninstall and reinstall from [docs.claude.com/claude-code](https://docs.claude.com/claude-code).
- `alwaysThinkingEnabled` isn't recognized → Your Claude Code is out of date. Update it.

---

**Next:** [Chapter 01 — Bootstrap a Repo](../01-bootstrap-a-repo/)
