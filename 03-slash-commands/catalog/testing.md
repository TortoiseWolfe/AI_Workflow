# Command Catalog — Testing

Commands that run tests inside Docker. All of them assume a containerized dev environment — you don't run tests on the host.

---

## `/test` — run the full suite

**Starter kit:** YES
**Scope:** personal
**File:** [`../starter-kit/.claude/commands/test.md`](../starter-kit/.claude/commands/test.md)

Detects the test runner from your package manifest (`package.json`, `pyproject.toml`, etc.) and runs the full suite inside the container via `docker compose exec <service> <runner>`.

Reports:
- Passing / failing / skipped counts
- Duration
- First failure message per failing test

**Does not attempt fixes.** This is a reporting command. If you want fixes, ask after you see the report.

**When to run:**
- Before `/commit` (or let `/commit` run lint + type-check and `/test` handle the rest)
- After pulling changes from a teammate
- When you're not sure if something's broken

---

## `/test-components` — components only

**Starter kit:** YES
**Scope:** personal

Runs only tests in `src/components/**/*.test.{ts,tsx}` or equivalent. Faster feedback loop during component work — you don't wait for full suite.

**Typical setup** in the command file:
```bash
docker compose exec <service> pnpm vitest run src/components --reporter=verbose
```

Add to your repo when component tests get slow enough that running the full suite hurts the feedback loop.

---

## `/test-a11y` — accessibility tests

**Starter kit:** YES
**Scope:** personal

Runs Pa11y, axe, or similar accessibility-focused tests. Separate command because these are often slow (they boot a browser) and you don't want them in your fast-feedback loop.

**Typical setup:**
```bash
docker compose exec <service> pnpm run test:a11y
```

Add when your project has accessibility tests. If you're building for WCAG AAA compliance (like ScriptHammer), this is mandatory before every ship.

---

## `/test-hooks` — hooks only

**Starter kit:** YES
**Scope:** personal

React hooks tests. A narrow slice of the suite for when you're iterating on hook logic.

```bash
docker compose exec <service> pnpm vitest run src/hooks --reporter=verbose
```

---

## `/test-fail` — re-run only failing tests

**Starter kit:** YES
**Scope:** personal

When `/test` reports failures, `/test-fail` re-runs **only** the failing tests. Much faster iteration during debug.

**Typical setup:**
```bash
docker compose exec <service> pnpm vitest run --testNamePattern "failing-test-name"
# OR use vitest's --related or --changed flags
```

Your test runner's docs will tell you the exact flag. Wire it into the command so you don't have to remember.

---

## The testing strategy

The starter kit only has `/test` because **on Day 1 you don't need granularity**. Run the full suite. It's fine.

Add the granular commands (`/test-components`, `/test-a11y`, `/test-hooks`, `/test-fail`) when:
- Your full suite takes > 30 seconds
- You're iterating on one area and don't care about the rest
- You're debugging flaky tests and need to narrow down

Don't add them preemptively. Premature command optimization is premature command optimization.

---

## Why all through Docker?

Three reasons:

1. **Reproducibility.** The container has the exact Node/Python/Go version your CI uses. Your host probably doesn't. Tests that pass locally but fail in CI are a nightmare — running inside Docker eliminates the gap.

2. **Permissions.** Docker volumes use the UID from your `.env`. Writing test artifacts (coverage reports, snapshots) goes to the right user. Running on the host can leave root-owned files that break your next `rm`.

3. **Dependencies.** Tests often need a running database, redis, etc. Docker Compose has those as sibling services. On the host you'd have to install and start them manually.

See [`principles/docker-first.md`](../../principles/docker-first.md) for the full argument.

---

## Related

- [quality.md](quality.md) — `/code-review` runs tests in Phase 4
- [git.md](git.md) — `/commit` runs lint + type-check before committing
- [`principles/docker-first.md`](../../principles/docker-first.md)
