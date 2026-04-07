# Knowledge Bases

The third layer of context: knowledge that doesn't belong in any single repo, but that you want Claude to know before you start working. Frameworks, best practices, expert transcripts, style guides from people smarter than you.

This is what [Claude Projects](https://claude.ai) are for — and it's a different tool from Claude Code. Worth understanding both.

---

## Where each layer lives

| Layer | Tool | What it's for |
|---|---|---|
| **1. Knowledge** | **Claude Projects** (claude.ai, the web app) | Background knowledge that applies to many projects |
| **2. Instructions** | **`CLAUDE.md`** (in your repo) | Rules specific to THIS project |
| **3. Operations** | **Slash commands** (`.claude/commands/*.md`) | Repeatable verbs you'll use repeatedly |

Claude Code (the CLI you've been using) handles layers 2 and 3. Claude Projects handles layer 1.

## What is a Claude Project?

On [claude.ai](https://claude.ai), you can create a "Project" — a persistent conversation workspace with:

- A **system prompt** you write once (think of it as a giant `CLAUDE.md` for layer 1)
- A **knowledge base**: files you upload that Claude reads every conversation in that Project

Use it for things like:

- "I want Claude to always critique my resume using these specific frameworks"
- "I want Claude to always follow these Docker best practices when I ask Dockerfile questions"
- "I want Claude to always remember these career-coaching frameworks when I ask for LinkedIn advice"

It is **not** for code-specific rules (those go in `CLAUDE.md`). It is for **reference material that makes Claude smarter about a topic**.

## The TranScripts pattern

TurtleWolfe maintains [`~/repos/TranScripts/`](https://github.com/TurtleWolfe/TranScripts), a library of cleaned YouTube transcripts organized by topic:

```
TranScripts/
├── Claude/
│   ├── Patterns/      # Claude Code workflow patterns
│   ├── Skills/        # Claude Code skills tutorials
│   └── Tools/         # Hooks, output styles, status lines
├── Docker/
│   └── Docker_Edited/ # Bret Fisher DockerCon talks, cleaned
├── Career/
│   ├── LinkedIn_Edited/   # LinkedIn profile frameworks
│   └── Resume_Edited/     # Resume writing frameworks
└── Drupal/
    └── Drupal_Edited/ # WebWash Drupal CMS tutorials
```

Each `*_Edited/` folder:
1. Contains YouTube transcripts **stripped of filler** (um, uh, intros, off-topic digressions)
2. Keeps **frameworks, actionable advice, templates, statistics**
3. Has a `*_SYSTEM_PROMPT.md` file that becomes the Claude Project's instructions

The setup: on claude.ai, create a new Project. Paste the `*_SYSTEM_PROMPT.md` as the Project Instructions. Upload the entire `*_Edited/` folder as the knowledge base. Now every conversation in that Project has expert knowledge baked in.

## Why this is valuable

Without a knowledge base, every time you ask Claude about Dockerfiles you get generic advice. With a knowledge base full of Bret Fisher's DockerCon talks, you get **Bret Fisher's opinionated specific advice**. Claude cites the transcripts. The quality of answers jumps dramatically.

Same for resume writing. Same for LinkedIn. Same for any domain where there's a specific expert or framework you want to emulate.

## How to build a knowledge base

The recipe TurtleWolfe uses:

1. **Find a subject expert on YouTube** you want to learn from
2. **Extract their transcripts** (via [mcp-youtube-transcript](https://github.com/jkawamoto/mcp-youtube-transcript) or manually)
3. **Clean them** — strip filler, keep frameworks. TurtleWolfe has a `/clean-transcript` slash command that does this automatically
4. **Organize by topic** in a repo
5. **Write a system prompt** that tells Claude to cite the transcripts when answering
6. **Upload to a Claude Project** at claude.ai

Full workflow in [`~/repos/TranScripts/README.md`](https://github.com/TurtleWolfe/TranScripts) if you want to steal it.

## When NOT to use a knowledge base

- **Code-specific rules.** Those go in `CLAUDE.md` in the actual repo.
- **Things that change often.** Knowledge bases are for stable reference material. Your team's evolving conventions should live in `CLAUDE.md`, not in a Project.
- **Sensitive data.** Don't upload secrets or personal data. Claude Projects are designed for reference material.
- **Anything small enough to paste.** If it fits in a message, paste it. Knowledge bases are for multi-file reference libraries.

## Claude Projects vs Claude Code — which to use?

| You're... | Use |
|---|---|
| Writing code in a specific repo | **Claude Code** with `CLAUDE.md` |
| Asking questions about a topic (career, Docker, a framework) | **Claude Projects** with a knowledge base |
| Doing both — writing code AND need expert background knowledge | **Both** — Claude Code for the repo, a Claude Project open in a browser tab for reference |

TurtleWolfe uses both, often in parallel. Code in Claude Code, tab over to Claude Projects to ask "what does Bret Fisher say about multi-stage builds?", paste the answer back into Claude Code as context for the next prompt.

---

## Related

- [writing-claude-md.md](writing-claude-md.md) — layer 2
- [priming-patterns.md](priming-patterns.md) — loading layer 2 into a session
- [`~/repos/TranScripts/README.md`](https://github.com/TurtleWolfe/TranScripts) — the reference implementation
- [Claude Projects documentation](https://docs.claude.com) — official docs
