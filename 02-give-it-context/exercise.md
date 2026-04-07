# Chapter 02 Exercise — Write a CLAUDE.md That Prevents a Mistake

**Time budget:** 30 minutes
**Success criterion:** You've written a `CLAUDE.md` for a real project, primed Claude with it, and confirmed Claude now handles a specific question correctly that it would have gotten wrong without the file.

---

## What you'll do

1. Pick a project (your `tsd-exercise-01` from Chapter 01, or any real repo you own)
2. Write a `CLAUDE.md` using the template
3. Identify ONE specific rule Claude would likely violate without the file
4. Run `/prep` in a fresh Claude session
5. Ask Claude a question that tests the rule
6. Confirm Claude got it right

## The steps

### 1. Pick a project (2 min)

Best choice: `tsd-exercise-01` from Chapter 01. It already has a `CLAUDE.md` from the starter — you're going to replace or extend it.

Alternative: any real project you own where you'd like Claude's help.

### 2. Copy the template (1 min)

```bash
cd ~/repos/tsd-exercise-01  # or your chosen project
cp ~/repos/AI_Workflow/01-bootstrap-a-repo/templates/CLAUDE.md.template ./CLAUDE.md
```

If the project already has a `CLAUDE.md`, back it up first:
```bash
cp CLAUDE.md CLAUDE.md.bak
cp ~/repos/AI_Workflow/01-bootstrap-a-repo/templates/CLAUDE.md.template ./CLAUDE.md
```

### 3. Fill in the template (10 min)

Open `CLAUDE.md` in your editor. Replace every `{{PLACEHOLDER}}` with a real value for your project:

- `{{PROJECT_NAME}}` — the actual name
- `{{STACK}}` — e.g., "Next.js 15 + React 19 + TypeScript + Tailwind 4"
- `{{DOCKER_SERVICE}}` — the service name from `docker-compose.yml`
- `{{pnpm | npm | pip | cargo}}` — pick one
- `{{Vitest | pytest | ...}}` — pick one

**Read [writing-claude-md.md](writing-claude-md.md) while you work** — use the three examples as reference.

**Keep it under 200 lines for this exercise.** Don't try to write a perfect masterpiece. A 100-line starter that covers the eight sections is plenty.

### 4. Pick one rule to test (5 min)

Look at your `CLAUDE.md`. Pick **one specific rule** that would NOT be obvious from reading the code alone. Examples:

- "Never install packages on the host, always use `docker compose exec`"
- "Use Vitest's `test()` not `it()` for test cases"
- "All components must be scaffolded with the 5-file atomic pattern, not as a single file"
- "Never import from `lodash`, use the native equivalent"
- "Secrets always go in `.env`, committed files use `${VAR:-placeholder}`"

**Write down the rule.** You're about to test it.

### 5. Test without context (3 min)

Open a fresh terminal. Navigate to the project. Launch Claude:

```bash
cd ~/repos/tsd-exercise-01
claude
```

**Do NOT run `/prep`.** Instead, ask a question where the obvious answer would violate your rule. Examples matching the rules above:

- "Install the `zod` package"
- "Write a test for the `formatDate` function"
- "Create a new `UserCard` component"
- "Add a utility to deep-clone an object"
- "Set the `DATABASE_URL` in the Docker Compose file"

**Observe Claude's response.** It will probably try to do the obvious thing — which violates your rule. Don't approve any edits. Say "stop" or press `Esc`.

Exit Claude: `/exit`.

### 6. Test WITH context (3 min)

Relaunch Claude:

```bash
claude
```

This time, run `/prep` first:

```
/prep
```

Expected output:
```
Read project context. Ready.
```

Now ask the **exact same question** from step 5. Observe the difference.

**Claude should now:**
- Follow your rule
- OR explain that it can't do what you asked without violating the rule, and offer the correct alternative

**If Claude still violates the rule**, your `CLAUDE.md` wasn't explicit enough. Go back to step 3 and sharpen the rule. Repeat.

### 7. Commit (1 min)

```
/commit
```

Land your new `CLAUDE.md`.

---

## Rubric

Check each box:

- [ ] Your `CLAUDE.md` exists and is 50-250 lines
- [ ] It has all eight sections (Header, Principles, Mandates, Commands, Stack, Structure, Testing, Deployment)
- [ ] Every `{{PLACEHOLDER}}` is replaced
- [ ] You ran Claude WITHOUT `/prep` and observed Claude violating a rule
- [ ] You ran Claude WITH `/prep` and observed Claude following the rule
- [ ] The new `CLAUDE.md` is committed

If any box is unchecked, the exercise isn't done. The point of this exercise is the *contrast* between the two sessions — feeling the difference between Claude without context and Claude with context is the point, not the words on the page.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Claude follows the rule even without `/prep` | Your rule is too obvious. Pick a rule that requires project-specific knowledge (e.g., "use pnpm not npm", "our linter forbids default exports") |
| Claude still violates the rule with `/prep` | Your rule isn't specific enough. Add the exact command or exact pattern. "Don't use npm" is weak; "Use `docker compose exec scripthammer pnpm` for all package operations" is strong |
| `/prep` outputs a summary instead of "Ready." | You're using a wrong `prep.md`. Re-copy from `03-slash-commands/starter-kit/.claude/commands/prep.md` |
| You ran out of time | Pick a shorter test rule. You don't need to write a perfect CLAUDE.md in 30 min — just prove the pattern works |

---

## What you learned

- `CLAUDE.md` is the difference between Claude guessing and Claude knowing
- Rules have to be specific — "use Docker" isn't a rule, "never run `pnpm install` on the host, only `docker compose exec scripthammer pnpm install`" is
- `/prep` is the switch that turns context on
- The template gets you 80% there; the remaining 20% is your specific project

---

**Next:** [Chapter 03 — Slash Commands](../03-slash-commands/)
