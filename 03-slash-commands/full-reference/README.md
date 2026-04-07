# Full Reference

The 10-command starter kit is what you need Day 1. But TurtleWolfe's full workflow uses **65 global commands + ~90 per-project commands**. The full library lives in its own backup repo:

> **Repo:** [`~/repos/Claude_Commandz`](https://github.com/TurtleWolfe/Claude_Commandz)

That repo is a **disaster-recovery mirror** of the live `~/.claude/commands/` directory and every tracked per-project `.claude/commands/` folder. It's keyed to TurtleWolfe's exact paths — you can't just `cp -a` it into your own setup and expect everything to work. Use it as a reference when you want to see how a specific command is structured.

---

## What's in there

From `Claude_Commandz/README.md`:

```
Claude_Commandz/
├── global/
│   ├── .claude/commands/         # 65 files — mirror of ~/.claude/commands/
│   └── dotfiles/                 # settings.json, statusline-command.sh
└── repos/
    ├── ScriptHammer/.claude/commands/                         (23 files)
    ├── TurtleWolfe/.claude/commands/                          (23 files)
    ├── good_prompt_bad_prompt/.claude/commands/               (14 files)
    ├── SpokeToWork---Business-Development/.claude/commands/   (13 files)
    ├── PeerMentor/.claude/commands/                            (8 files)
    ├── TranScripts/.claude/commands/                           (7 files)
    ├── KDG/.claude/commands/                                   (1 file)
    └── drupal-v2-sandbox/.claude/commands/                     (1 file)
```

**Totals:** 65 global commands + 2 dotfiles + 90 project commands across 8 repos = 157 backed-up files.

## The 65 global commands, roughly grouped

**Priming / context** — `prep`, `prime`, `prime_repositories`
**SpecKit** — `constitution`, `specify`, `clarify`, `plan`, `tasks`, `analyze`, `implement`, plus the `speckit.*` variants
**Git / shipping** — `commit`, `ship`
**Quality** — `code-review`, `security-audit`, `secrets-scan`
**Testing** — `test`, `test-a11y`, `test-components`, `test-hooks`, `test-fail`
**Orchestration** (Chapter 05) — `dispatch`, `queue`, `queue-check`, `review-queue`, `status`, `next`, `log`, `refresh-inventories`
**Wireframe pipeline** (Chapter 05) — `wireframe`, `wireframe-plan`, `wireframe-prep`, `wireframe-focused`, `wireframe-fix`, `wireframe-review`, `wireframe-inspect`, `wireframe-screenshots`, `wireframe-status`, `hot-reload-viewer`, `viewer-status`
**Governance / RFCs** (Chapter 05) — `rfc`, `rfc-vote`, `vote-now`, `council`, `broadcast`, `memo`, `audit`, `constitution`
**Session** — `session-stats`, `session-summary`, `clean-start`
**Utilities** — `clean-transcript`, `extract-linkedin`, `rpg_subsystem_scaffold`, `read-spec`, `read-issues`, `secrets-scan`

You will recognize maybe 15 of these from the starter kit + Chapter 05. The rest are situational, one-off, or TurtleWolfe-specific.

---

## How to steal specific commands

If you want one of TurtleWolfe's commands:

1. **Find it** in `~/repos/Claude_Commandz/global/.claude/commands/`
2. **Read it** — understand what it does before adopting it
3. **Copy it** to your own `~/.claude/commands/<name>.md` (global) or `<project>/.claude/commands/<name>.md` (per-project)
4. **Adapt it** — replace hardcoded paths, adjust service names in Docker commands, remove references to infrastructure you don't have
5. **Test it** — run it in a throwaway scenario before relying on it

**Do NOT** copy commands wholesale without reading them first. Some commands (`/dispatch`, `/queue`) assume the 27-terminal tmux infrastructure. Some (`/wireframe`) assume a specific SVG validator script. They won't work in your repo without the supporting cast.

## How to keep your own backup

The pattern from `Claude_Commandz/README.md`:

```bash
# In your own backup repo
mkdir -p global/.claude/commands global/dotfiles

# Refresh: copy from live system
cp -a ~/.claude/commands/. global/.claude/commands/
cp ~/.claude/settings.json global/dotfiles/settings.json

# Per-project (loop over existing repos)
for d in repos/*/; do
  name=$(basename "$d")
  src=~/repos/"$name"/.claude/commands
  [ -d "$src" ] && cp -a "$src/." "$d/.claude/commands/"
done

# Commit
git add -A
git commit -m "refresh: sync command backups"
```

Run this periodically. Secrets stay out (`settings.json` doesn't contain any — enforce this), per-project customizations stay in. If your machine dies, clone the backup, run the restore in reverse, and you're back in business.

---

## Related

- [Chapter 03 — Slash Commands](../README.md) — the Day-1 starter kit
- [`~/repos/Claude_Commandz/README.md`](https://github.com/TurtleWolfe/Claude_Commandz) — the full backup repo
- [Chapter 05 — Advanced Orchestration](../../05-advanced-orchestration/) — most of the 65 commands only make sense in this context
