# Installing Claude Code

This is a pointer, not a tutorial. Anthropic owns the installation docs and they change. **Always start here:**

> **Official docs:** [https://docs.claude.com/claude-code](https://docs.claude.com/claude-code)

## What to ignore in the official docs on Day 1

The official docs cover many features you do not need yet. Install Claude Code, make `claude --version` work, and come back to this repo.

You can ignore (for now):

- MCP servers
- Custom hooks
- IDE integrations (VS Code, JetBrains)
- Output styles
- Team/workspace features

## What to confirm before leaving this page

Open a terminal and run each of these. All three should succeed:

```bash
claude --version            # prints a version number
claude --help               # prints help text
claude                      # launches the REPL; type /help, then /exit
```

If all three work, you're done. Go to [Chapter 01](../01-bootstrap-a-repo/).

## Common install errors

| Error | Usual cause | Fix |
|---|---|---|
| `command not found: claude` | Not installed, or `PATH` doesn't include the install location | Follow the official installer again; restart your shell |
| `claude: permission denied` | Binary isn't executable | `chmod +x $(which claude)` |
| Works in one terminal, not another | One terminal loaded your shell rc before install | Open a fresh terminal |

If you're stuck, **do not debug for more than 10 minutes**. Ask your mentor. Install problems are almost always environment-specific and not worth solo-debugging on Day 1.

---

**Next:** [first-conversation.md](first-conversation.md)
