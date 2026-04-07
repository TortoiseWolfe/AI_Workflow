---
description: Perform a comprehensive code review covering security, performance, code quality, and test coverage
scope: personal
---

Execute a systematic code review of the current working tree. **FIX issues directly rather than documenting them**, unless the user asks for a report-only review.

## Output Constraints

- Bullet points only, no prose explanations
- One summary table at the end, not per-phase
- Skip "next steps" unless errors block progress
- No redundant confirmations

## First — Detect the Stack

Identify the test runner, package manager, and linter from `package.json` / `pyproject.toml` / `go.mod`. All subsequent commands run inside Docker if the project is Docker-first.

## Phase 1: Security Audit

1. **Secrets in committed files**
   - Search: API keys, tokens, credentials, passwords
   - Verify: All secrets in environment variables (`.env`, gitignored)
   - Check: No hardcoded values in `docker-compose.yml`, scripts, or source
   - FIX: Move to `.env`, replace with `${VAR:-placeholder}`

2. **Authentication & authorization**
   - Search: `getUser`, `getSession`, `req.user`, auth middleware
   - Verify: All sensitive routes check authentication
   - Check: CSRF protection on state-changing operations
   - FIX: Add missing auth checks

3. **SQL/NoSQL injection**
   - Search: Raw queries, string concatenation in queries
   - Verify: Parameterized queries or ORM used
   - Check: User input never directly in query strings
   - FIX: Parameterize any raw queries

4. **XSS vulnerabilities**
   - Search: unsafe HTML injection APIs, user-content rendering without sanitization
   - Verify: a sanitization library is in use (DOMPurify, sanitize-html, etc.)
   - FIX: Sanitize or escape any rendered user content

## Phase 2: Performance

1. **Expensive operations without memoization**
   - Search: Large components without `React.memo` / `useMemo`
   - Search: Repeated regex on user input, repeated network calls
   - FIX: Add caching/memoization where missing

2. **N+1 queries and polling**
   - Search: Loops containing database queries, `setInterval` polling patterns
   - FIX: Batch queries, convert polling to realtime where appropriate

## Phase 3: Code Quality

1. **Duplicate files** — find files with similar names/content, delete duplicates
2. **Linter disables** — review every `eslint-disable` / `@ts-ignore` / `# noqa` for legitimacy, fix underlying issue when possible
3. **TODO comments** — resolve quick fixes, create issues for complex ones
4. **Unimplemented stubs** — `throw new Error('Not implemented')`, empty bodies — implement or remove
5. **Dead code** — unused exports, unreachable code, commented-out code — delete

## Phase 4: Test Coverage

1. **Untested modules** — list files in `services/`, `lib/`, `utils/`, check for corresponding test files, create tests for critical untested code
2. **Skipped tests** — investigate every `.skip`, enable or delete with explanation
3. **Test quality** — run the project test suite, report pass/fail counts

## Phase 5: Output

End with ONE summary table:

| Category | Found | Fixed | Remaining |
|---|---|---|---|
| Security | X | Y | Z |
| Performance | X | Y | Z |
| Code Quality | X | Y | Z |
| Test Coverage | X | Y | Z |

**CRITICAL:** Fix issues directly. Do not defer work to "later" or create issues as a way to avoid fixing things.
