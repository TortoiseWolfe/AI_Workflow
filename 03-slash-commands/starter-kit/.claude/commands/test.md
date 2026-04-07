---
description: Run the comprehensive test suite to diagnose code quality issues and failures
scope: personal
---

Run the project's full test suite and report results.

## Docker-First Requirement

**CRITICAL:** If the project has a `docker-compose.yml` or `CLAUDE.md` mentioning Docker-first development, ALL test commands run inside the container via `docker compose exec <service>`.

## Instructions

1. **Detect the test runner** from `package.json` (scripts.test), `pyproject.toml`, `go.mod`, or `Cargo.toml`.

2. **Ensure the container is running** (Docker-first projects):
   ```bash
   docker compose ps
   # If the service isn't up:
   docker compose up -d
   ```

3. **Run the test suite** inside the container:
   ```bash
   # Node (most common in this workflow)
   docker compose exec <service> pnpm test

   # Python
   docker compose exec <service> pytest

   # Go
   docker compose exec <service> go test ./...

   # Rust
   docker compose exec <service> cargo test
   ```

4. **Parse the output**:
   - Count passing / failing / skipped tests
   - Identify which test files have failures
   - Extract the first failure message (usually the most informative)

5. **Report** in this format:
   ```
   Test Results
   ────────────
   Passing:  123
   Failing:    2
   Skipped:    5
   Duration:   12.3s

   Failing tests:
   1. src/components/Button/Button.test.tsx — "renders with disabled state"
      Expected: true
      Received: false

   2. src/lib/auth.test.ts — "refresh token before expiry"
      Timeout after 5000ms
   ```

6. **Do NOT attempt to fix failures in this command.** Just report. If the user wants fixes, they'll ask.

## Related Commands

- `/test-a11y` — Pa11y accessibility tests only (if project has them)
- `/test-components` — component tests only
- `/test-hooks` — hook tests only
- `/test-fail` — re-run only previously failing tests
- `/code-review` — comprehensive review beyond just tests
