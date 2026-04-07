# Chapter 01 Exercise — Ship Your First AI-Assisted Commit

**Time budget:** 15 minutes
**Success criterion:** `git log -1` shows a commit you made with Claude's help, containing a real change to `src/app/page.tsx`, with the Claude Code co-author footer.

---

## What you'll do

1. Clone `hello-world-ai` and rename it
2. Boot it under Docker
3. Use `/prep` to prime Claude
4. Ask Claude to make an edit
5. Use `/commit` to ship it

If you did [clone-the-starter.md](clone-the-starter.md) already, you're done — come back and check the rubric below.

## The steps

### 1. Clone (3 min)

```bash
cd ~/repos
git clone <hello-world-ai-url> tsd-exercise-01
cd tsd-exercise-01
```

If you don't have a clone URL yet, ask your mentor. Or locally:

```bash
cp -a ~/repos/hello-world-ai ~/repos/tsd-exercise-01
cd ~/repos/tsd-exercise-01
rm -rf .git && git init && git add -A && git commit -m "chore: initial import"
```

### 2. Rename (2 min)

Edit `package.json` and `docker-compose.yml`. Find `hello-world-ai`, replace with `tsd-exercise-01`.

### 3. Boot (3 min)

```bash
cp .env.example .env
docker compose up
```

Wait for the "ready" line. Open [http://localhost:3000](http://localhost:3000) in a browser. Confirm you see the landing page.

### 4. Prime and edit (4 min)

In another terminal:

```bash
cd ~/repos/tsd-exercise-01
claude
```

Inside Claude:

```
/prep
```

Expected output:
```
Read project context. Ready.
```

Now ask:
```
Change the h1 text on src/app/page.tsx from "Hello, TSD" to a greeting that includes your actual name.
```

Claude reads the file, shows you the diff, applies it. The browser hot-reloads.

### 5. Ship (3 min)

Still inside Claude:

```
/commit
```

Watch lint and type-check run inside the container. Watch the commit land.

### Verification

Exit Claude (`/exit`). In the shell:

```bash
git log -1
```

You should see:

```
commit <hash>
Author: You <you@example.com>

    feat: personalize landing greeting

    🤖 Generated with [Claude Code](https://claude.com/claude-code)

    Co-Authored-By: Claude <noreply@anthropic.com>
```

**If you see this, you've completed Chapter 01.** ✓

---

## Rubric

Check each box before moving to Chapter 02:

- [ ] `git log -1` shows a real commit
- [ ] The commit touches `src/app/page.tsx`
- [ ] The commit message uses conventional-commit format (`feat:`, `fix:`, etc.)
- [ ] The commit message has the Claude Code footer
- [ ] `docker compose up` still shows the dev server running
- [ ] The browser reflects your edit

If any box is unchecked, re-read the relevant step and try again. Don't move on with a half-working setup — Chapter 02 assumes Chapter 01 worked.

---

## If it didn't work

| Problem | Most likely cause |
|---|---|
| `/prep` dumps a whole summary | You're editing the wrong `prep.md` file — it should be 12 lines, not 100. Copy it fresh from `hello-world-ai/.claude/commands/prep.md`. |
| `/commit` fails on lint | Read the lint error. Ask Claude: `fix the lint error`. Re-run `/commit`. |
| `docker compose up` says "no service named ..." | You renamed `hello-world-ai` in `docker-compose.yml` but not consistently. Re-check the service name. |
| The commit has no Claude Code footer | You're probably on an old version of `.claude/commands/commit.md`. Check it matches `AI_Workflow/03-slash-commands/starter-kit/.claude/commands/commit.md`. |

---

**Next:** [Chapter 02 — Give It Context](../02-give-it-context/)
