# Clone the Starter

The fastest path from zero to a working AI-assisted project. Clone `hello-world-ai`, rename it, boot it, ship a commit. Under 15 minutes.

---

## Prerequisites

- [Docker Desktop](https://docs.docker.com/get-docker/) running (check: `docker ps` returns without error)
- [Claude Code](https://docs.claude.com/claude-code) working (check: `claude --version`)
- A terminal in your `~/repos/` directory (or wherever you keep projects)

If `docker ps` errors out, start Docker Desktop first.

## Step 1 — Clone

```bash
cd ~/repos
git clone <your-mentor-gives-you-this-url> my-first-ai-project
cd my-first-ai-project
```

Replace `my-first-ai-project` with whatever name you want for your project.

> **Note for the curriculum author:** until `hello-world-ai` is pushed to a GitHub URL, copy it locally:
> ```bash
> cp -a ~/repos/hello-world-ai ~/repos/my-first-ai-project
> cd ~/repos/my-first-ai-project
> rm -rf .git
> git init
> git add -A
> git commit -m "chore: initial import from hello-world-ai starter"
> ```

## Step 2 — Rename the project

Two files mention the old name and need updating:

```bash
# Open in your editor, find-and-replace "hello-world-ai" → "my-first-ai-project"
$EDITOR package.json docker-compose.yml
```

Specifically:
- `package.json` — the `name` field
- `docker-compose.yml` — the `services` key and any container names

Save both files.

## Step 3 — Set up environment

```bash
cp .env.example .env
```

`.env` is gitignored. For `hello-world-ai` you don't need to fill anything in — the defaults work.

## Step 4 — Boot under Docker

```bash
docker compose up
```

First boot takes a minute or two (pulling images, installing dependencies). You're looking for a line that says the Next.js dev server is ready, like:

```
▲ Next.js 15.x.x
- Local:        http://localhost:3000
- ready started server on 0.0.0.0:3000
```

Open [http://localhost:3000](http://localhost:3000) in a browser. You should see the "Hello, TSD" landing page.

## Step 5 — Prime Claude and make an edit

In a second terminal, still inside `my-first-ai-project`:

```bash
claude
```

At the Claude prompt, run:

```
/prep
```

You should see only:

```
Read project context. Ready.
```

That's the `/prep` command — it reads your new `CLAUDE.md` silently so Claude knows the rules before you ask anything. (Full explanation in [Chapter 02](../02-give-it-context/).)

Now ask Claude to make a trivial change:

```
change the h1 on src/app/page.tsx from "Hello, TSD" to "Hello, [your name]"
```

Claude reads the file, proposes an edit, and applies it. The browser hot-reloads — you should see your name on the page.

## Step 6 — Ship the commit

Still in Claude:

```
/commit
```

`/commit` runs lint and type-check inside the Docker container, then creates a conventional commit with the Claude Code co-author footer. You'll see:

```
✓ Lint passed
✓ Type-check passed
✓ Committed: feat: personalize landing page
```

Run `git log -1` to confirm the commit landed.

**You're done.** 15 minutes from zero to a shipped commit.

---

## What you just did

1. Cloned a working Docker-first Next.js starter
2. Renamed it
3. Booted it with one command
4. Primed Claude with your project's rules via `/prep`
5. Asked Claude to make an edit
6. Shipped the commit via `/commit`

Every project you start from here on out will follow the same shape: **clone → prime → ask → ship.** Chapters 02-04 explain each step in depth.

---

## If something broke

| Symptom | Fix |
|---|---|
| `docker compose up` fails with port 3000 in use | Stop whatever else is on 3000 (`lsof -i :3000`), or change the port mapping in `docker-compose.yml` |
| Browser shows "cannot connect" | Wait 60 seconds — first boot is slow. Then check terminal for errors. |
| `/prep` outputs a summary instead of just "Ready." | You skipped or modified `.claude/commands/prep.md`. Copy it fresh from `~/repos/hello-world-ai/.claude/commands/prep.md` |
| `/commit` fails on lint | Read the lint error, ask Claude to fix it, re-run `/commit` |
| `/commit` fails on type-check | Same — Claude will fix it |
| Hot reload doesn't work | Docker volume mounting on WSL can be slow. Save the file, wait 10 seconds. |

---

**Next:** [exercise.md](exercise.md)
