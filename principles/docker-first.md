# Principle — Docker-First

> **Rule:** Never run package managers, build tools, test runners, or development servers on the host. All commands run inside containers via `docker compose exec <service> <command>`.

---

## Why

### The war story

A new contributor cloned ScriptHammer, ran `pnpm install` on the host, then ran `docker compose up`. The container booted, Docker mounted the project directory in, and now the container was looking at a `node_modules/` that was installed for the host's Node version (22.x), not the container's (also 22.x — but compiled against musl, not glibc).

**Symptoms:**
- `sharp` (image processing) crashed at boot with "wrong ELF class"
- `bcrypt` couldn't load its native binding
- `next dev` started but every page that imported either of those crashed
- The error messages were Node-internal, not application-level — "ENOENT" pointing at files that existed

The "fix" attempt: `sudo rm -rf node_modules` on the host. **This failed** because Docker had created files inside `node_modules/.cache/` as the container's user (UID 1000 from the .env file, which happened to match the host user, but Docker had set them as root-owned for some intermediate operations). Now `sudo` was required to clean up Docker-owned files. Now the user was sudoing in their project directory. Now permissions were getting weirder.

**Real fix:**
```bash
docker compose down
docker compose run --rm scripthammer rm -rf node_modules
docker compose up
```

That's the Docker-first path: ask the container to clean up the container's mess. Never ask the host.

The contributor lost 90 minutes diagnosing this. They could have lost 0 minutes by running `docker compose exec scripthammer pnpm install` instead of `pnpm install` on the host.

### The general principle

Containers exist to provide a **reproducible environment**. The moment you run any tool on the host, you've broken reproducibility:

- Your Node version may differ from the container's
- Your package manager (pnpm/npm/yarn) may differ
- Your file permissions belong to your host user, not the container user
- Your Python venv leaks into the container's `site-packages` if it's mounted
- Your `.cache/` directories grow with files Docker doesn't know about

These divergences are **invisible** until they break something. And when they break, the error messages are unhelpful because the diagnosis is "your host and your container disagree about reality" — which is hard to express as a useful log line.

Docker-first eliminates the entire class of problems by **never letting the host touch the project except via the container**.

---

## How to apply

### The rules

1. **All package operations run via Docker.**
   ```bash
   # NEVER on the host
   pnpm install
   pnpm add zod

   # ALWAYS via Docker
   docker compose exec scripthammer pnpm install
   docker compose exec scripthammer pnpm add zod
   ```

2. **All test runs go via Docker.**
   ```bash
   # NEVER on the host
   pnpm test
   pnpm vitest run

   # ALWAYS via Docker
   docker compose exec scripthammer pnpm test
   ```

3. **All build commands go via Docker.**
   ```bash
   # NEVER on the host
   pnpm run build

   # ALWAYS via Docker
   docker compose exec scripthammer pnpm run build
   ```

4. **Slash commands enforce this.** `/commit`, `/test`, `/code-review`, `/ship`, and `/clean-start` all run their commands inside Docker. If you write your own slash command, follow the same pattern.

5. **Permission errors → use Docker, never `sudo`.**
   ```bash
   # NEVER
   sudo chown -R $USER:$USER node_modules

   # ALWAYS
   docker compose exec scripthammer rm -rf node_modules
   docker compose down && docker compose up
   ```

### Exceptions

The only commands that legitimately run on the host:
- `git` (Git is a host tool, files are mounted into Docker)
- `docker compose` itself
- Editor commands (`code`, `vim`, etc.)
- Operating system commands (`ls`, `cd`, `cat` of source files)

If you find yourself running a build/test/lint/install command on the host, **stop**. Use Docker.

### Setting it up in a new project

1. **`docker-compose.yml`** at repo root with at least one service for the app
2. **`Dockerfile`** that installs dependencies and copies source
3. **`.dockerignore`** that excludes `node_modules/`, `.next/`, etc.
4. **`CLAUDE.md`** with a "Docker-First" section that prohibits host commands explicitly
5. **`.env.example`** committed; `.env` gitignored
6. **Slash commands** that run via `docker compose exec`

The [`01-bootstrap-a-repo/templates/`](../01-bootstrap-a-repo/templates/) directory has the templates for all of these.

---

## When NOT to apply

There are projects where Docker-first is the wrong call:

- **Mobile apps (iOS, Android).** ScanDo (the LiDAR app) is React Native + Swift native modules. iOS builds happen on macOS or in EAS Cloud, not in Docker. ScanDo's `CLAUDE.md` explicitly says "NOT Docker-first."
- **Native desktop apps** with platform-specific build chains
- **Hardware projects** where the dev environment IS the host's USB stack
- **Performance-critical local benchmarks** where Docker's overhead would distort results

For these, document the exception in the project's `CLAUDE.md` so Claude doesn't try to apply the Docker-first rule incorrectly.

---

## Related

- [`secrets-never-committed.md`](secrets-never-committed.md) — another mandatory rule
- [`01-bootstrap-a-repo/templates/docker-compose.yml.template`](../01-bootstrap-a-repo/templates/docker-compose.yml.template) — the starter template
- [`03-slash-commands/catalog/git.md`](../03-slash-commands/catalog/git.md) — `/commit` and `/ship`, both Docker-first
- [`03-slash-commands/catalog/testing.md`](../03-slash-commands/catalog/testing.md) — testing commands, all Docker-first
