# Chapter 03 Exercise — Install the Starter Kit and Write Your First Custom Command

**Time budget:** 30 minutes
**Success criterion:** All 30 starter-kit commands installed in a project of yours, AND you have written one new custom command that automates a prompt you've typed at least twice.

---

## Part 1 — Install the starter kit (10 min)

### 1. Pick a project

Use `tsd-exercise-01` from Chapter 01, or any real repo where you'll use Claude Code:

```bash
cd ~/repos/tsd-exercise-01
mkdir -p .claude/commands
```

### 2. Copy all 30 starter-kit commands

```bash
cp ~/repos/TSD_AI_Workflow/03-slash-commands/starter-kit/.claude/commands/*.md \
   .claude/commands/
```

### 3. Verify they loaded

```bash
claude
```

Inside Claude, type `/` and look at the command list. You should see all 30 commands. Test the simplest one:

```
/prep
```

Expected: `Read project context. Ready.`

Then test a few from each family:

| Test | Family | What you should see |
|---|---|---|
| `/test` | Testing | Lists test runner detected, runs the suite |
| `/code-review` | Quality | Starts a 5-phase audit of the working tree |
| `/status` | Session | Repo health summary |

### 4. (Optional) Initialize SpecKit

If you plan to use the 10 SpecKit commands (`/speckit.specify` etc.), initialize SpecKit in this project:

```bash
# Outside Claude, in the same directory:
uvx --from git+https://github.com/github/spec-kit.git@v0.5.0 specify init
```

This creates `.specify/` with the scripts and templates the SpecKit commands depend on. Skip this step if you only want the non-SpecKit families today.

### 5. Commit the starter kit

Back inside Claude:
```
/commit
```

You should see lint + type-check run, then a commit land with a message like `chore: install 30-command starter kit`.

---

## Part 2 — (Optional) Install the full 65-command kit (5 min)

If you want the orchestration, governance, wireframe pipeline, and knowledge curation commands (Chapter 05 territory), run the install script:

```bash
bash ~/repos/TSD_AI_Workflow/03-slash-commands/install-full-kit.sh
```

This copies the remaining 35 commands from `~/repos/Claude_Commandz/global/.claude/commands/` into your **global** `~/.claude/commands/` (not per-project — these are personal commands).

You only do this once, ever. After this you have all 65 of TurtleWolfe's commands available globally.

> **Don't run this on Day 1 unless you know you need it.** Most of these commands need infrastructure that doesn't exist in your project yet (the 27-terminal tmux session, the wireframe validator script, etc.). They'll show up in `/help` but won't *do* anything useful until you set up Chapter 05.

---

## Part 3 — Write your own command (15 min)

### 1. Identify a repetitive prompt

Think back to the last 5-10 sessions with Claude Code. What's a prompt you've typed more than once? Candidates:

- "Show me every TODO comment in the codebase"
- "List all files larger than 500 lines"
- "Find every component without a test file"
- "Show me the last 10 failing test runs"
- "Scaffold a new component with the 5-file pattern"
- "Run `docker compose down && docker compose up --build`"
- "Generate the weekly standup summary from git log"

**Pick one.** If you don't have a repetitive prompt yet (Day 1!), pick "Show me every TODO comment" — that's a good starter.

### 2. Sketch the command

Create `.claude/commands/<your-command-name>.md`:

```bash
$EDITOR .claude/commands/find-todos.md
```

Use this skeleton:

```markdown
---
description: One-sentence description shown in the command list
scope: personal
---

Short prose explaining what this command does and why.

## Instructions

1. Step one — specific action
2. Step two — specific action
3. Step three — specific action

## Output

What Claude should report when done. Be specific.

## Notes

- Any edge cases
- When NOT to use this command
```

### 3. Write the command body

For the "find TODOs" example:

```markdown
---
description: List every TODO, FIXME, HACK, and XXX comment in the codebase with file:line
scope: personal
---

Find all marker comments and report them in a browsable list.

## Instructions

1. Search the repo (excluding node_modules, .next, dist, build) for comments containing:
   - TODO
   - FIXME
   - HACK
   - XXX
   - BUG

2. For each match, capture:
   - File path
   - Line number
   - The comment text

3. Group matches by file and sort by file path.

4. For each file, list the matches indented under it with the file:line format so the user can click to jump.

## Output

Format:

\`\`\`
src/lib/auth.ts
  src/lib/auth.ts:42 — TODO: handle refresh token expiry
  src/lib/auth.ts:87 — FIXME: race condition on concurrent logout

src/components/Button/Button.tsx
  src/components/Button/Button.tsx:15 — HACK: inline styles until theme lands
\`\`\`

End with a count: `Found N markers in M files.`

If no matches, report `No marker comments found.`

## Notes

- Exclude third-party code (node_modules, vendor/, etc.)
- Do not fix the TODOs — this is a report-only command
```

### 4. Test your command

Back in Claude:

```
/find-todos
```

(or whatever you named it)

Claude should follow the instructions and produce the output format you specified.

**If it doesn't work exactly right**, the problem is almost always vague instructions. Sharpen them and try again. This is the core skill: writing commands specific enough that Claude behaves the same every time.

### 5. Commit your new command

```
/commit
```

You should see a commit like `feat: add /find-todos command`.

---

## Rubric

- [ ] All 30 starter-kit commands live in your project's `.claude/commands/`
- [ ] `/prep`, `/commit`, `/test` all work without errors
- [ ] You wrote a new `.md` file in `.claude/commands/` with frontmatter (`description`, `scope`)
- [ ] Your new command has an `## Instructions` section with numbered steps
- [ ] Your new command has an `## Output` section describing the expected result
- [ ] Your new command runs successfully and produces output matching what you specified
- [ ] Both the starter kit AND your new command are committed

If any box is unchecked, the exercise isn't done.

---

## What you learned

- Slash commands are just markdown files. There's no framework, no API, no compiler. Write a file, use it.
- Specificity is everything. "Find TODOs" is vague. "Search excluding node_modules, group by file, format as file:line" is a command.
- The starter kit is the starter kit because you'll use it daily. Your custom commands grow from pain — every command you write solves a repeated annoyance.
- The full 65-command kit is one script away. Don't install it until you need it.

---

**Next:** [Chapter 04 — The SpecKit Loop](../04-the-speckit-loop/)
