# CLAUDE.md

Instructions for Claude Code when editing **this teaching repo**.

## What this repo is

`AI_Workflow` is a curriculum that teaches TSD interns how TurtleWolfe uses Claude Code. It is **documentation and exercises**, not code. Source of truth for the structure lives at `/home/TurtleWolfe/.claude/plans/snuggly-jumping-yao.md`.

## Non-negotiables

### 1. Preserve the "Day-1 minimum / dig-deeper" structure

Every chapter must be usable by reading only the first 2 pages. If you add content, put it below the **Dig deeper** fold — not in the introduction. The entire point of this repo is that an overwhelmed intern can skim and still be productive.

**Test:** Would a new intern with 15 minutes of attention finish the exercise after reading only the intro section? If no, move content below the fold.

### 2. The starter kit is 30 commands across 7 families — do not pad, do not gimp

The 30-command starter kit in `03-slash-commands/starter-kit/.claude/commands/` is:

```
priming (3)        prep, prime, prime_repositories
speckit (10)       speckit.specify, speckit.clarify, speckit.plan, speckit.tasks,
                   speckit.implement, speckit.analyze, speckit.checklist,
                   speckit.constitution, speckit.taskstoissues, speckit.workflow
git (2)            commit, ship
quality (4)        code-review, security-audit, secrets-scan, audit
testing (5)        test, test-a11y, test-components, test-fail, test-hooks
session (4)        session-stats, session-summary, status, clean-start
reading (2)        read-spec, read-issues
```

These are **byte-identical copies of the live `~/.claude/commands/` versions** as of when the curriculum was authored. Refresh from `~/.claude/commands/` if they drift. **Do not edit them in place** — edit the source, then re-copy.

**Excluded from the starter kit (live in Chapter 05 or `install-full-kit.sh`):**
- Orchestration: `dispatch`, `queue`, `queue-check`, `review-queue`, `next`, `log`, `refresh-inventories`
- Governance: `rfc`, `rfc-vote`, `vote-now`, `council`, `broadcast`, `memo`
- Wireframe pipeline: `wireframe*` (11 commands), `hot-reload-viewer`, `viewer-status`
- Knowledge curation: `clean-transcript`, `extract-linkedin`, `rpg_subsystem_scaffold`
- Archived: `wireframe-v3-archived`
- Legacy SpecKit aliases (bare-name `specify`, `clarify`, `plan`, etc.): superseded by `speckit.*`, intentionally NOT shipped

If you are tempted to add a 31st command to the starter kit, ask first. The split between starter kit and Chapter 05 is by **infrastructure dependency**, not popularity:

- **Starter kit** = commands that work in any Docker-first project with Claude Code installed
- **Chapter 05** = commands that need additional infrastructure (tmux session, terminal roles, validator scripts, viewer containers)

If a new command needs no extra infrastructure, it might belong in the starter kit. Otherwise, document it in `catalog/` or `05-advanced-orchestration/`.

### 3. Do not leak Chapter 05 examples into earlier chapters

Chapter 05 (the 27-terminal tmux assembly line) is **Level 3 / Optional**. Chapters 00-04 must be completable by someone who never opens Chapter 05. If an example requires `tmux`, `/dispatch`, `/queue`, `/rfc`, or terminal roles, it belongs in Chapter 05, not earlier.

**Violation check:** grep for `tmux`, `/dispatch`, `/rfc` in chapters 00-04. These words should only appear as cross-references pointing *at* Chapter 05, never as required steps.

### 4. Every chapter ends with exactly one 15-minute exercise

Not two. Not a list. **One exercise** with:

- A clear success criterion (a file exists, a command passes, a commit lands)
- A time budget stated in the header
- A "if this failed, check:" troubleshooting list

Exercises live at `NN-chapter/exercise.md`.

### 5. Every principle has a war story

Files in `principles/` must justify the rule with a concrete incident or consequence, not just state it. "Don't commit secrets" is not a principle file. "Don't commit secrets — last year a JWT leaked into a public repo via a demo compose file and we had to `git-filter-repo` a 200-commit history" is a principle file.

If you can't find a war story, the rule probably shouldn't be in `principles/`.

### 6. Use real examples from real repos

When showing a `CLAUDE.md` example, pull an annotated excerpt from an actual repo (ScriptHammer, TurtleWolfe, SpokeToWork, KDG). Do not invent toy examples. The intern should see code that ships to production, not code that exists only in this tutorial.

**Real repos to pull from:**
- `/home/TurtleWolfe/repos/ScriptHammer/CLAUDE.md`
- `/home/TurtleWolfe/repos/TurtleWolfe/CLAUDE.md`
- `/home/TurtleWolfe/repos/SpokeToWork/CLAUDE.md`
- `/home/TurtleWolfe/repos/CLAUDE.md` (workspace index)
- `/home/TurtleWolfe/repos/Claude_Commandz/global/.claude/commands/*.md`

## File shape conventions

- Chapter README.md at `NN-name/README.md` — the landing page for that chapter
- Content files at `NN-name/topic.md` — deeper material, one topic per file
- Exercise at `NN-name/exercise.md` — always named `exercise.md`
- Max file length: ~300 lines. If you need more, split into a second file.
- Use lowercase-with-hyphens for file names (`writing-claude-md.md`, not `WritingClaudeMd.md`)
- Frontmatter is optional — most files don't need it

## Editing etiquette

- **Do not rewrite existing chapters to match a new idea.** If a new insight doesn't fit the existing structure, add a new file or amend the relevant principle. Don't restructure what already works.
- **Do not add emojis unless requested.** This repo ships to professional interns.
- **Do not add installation instructions for tools Anthropic already documents.** Link to `docs.claude.com/claude-code`, don't re-document it.
- **Do not create new chapters.** Six chapters plus `principles/`. If you think there should be a seventh, flag it to the user — don't just add it.

## Related docs

- Plan file (source of truth for structure): `/home/TurtleWolfe/.claude/plans/snuggly-jumping-yao.md`
- Companion starter repo: `/home/TurtleWolfe/repos/hello-world-ai`
- Workspace CLAUDE.md: `/home/TurtleWolfe/repos/CLAUDE.md`
- Full command backup: `/home/TurtleWolfe/repos/Claude_Commandz`
