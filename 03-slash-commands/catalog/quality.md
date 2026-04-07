# Command Catalog — Quality

Commands that audit your code for issues you didn't write on purpose. Run these before shipping, and occasionally as a health check on existing code.

---

## `/code-review` — comprehensive audit

**Starter kit:** YES
**Scope:** personal
**File:** [`../starter-kit/.claude/commands/code-review.md`](../starter-kit/.claude/commands/code-review.md)

A 5-phase review that finds AND fixes issues (not just reports them):

1. **Security** — secrets, auth, injection patterns, unsafe HTML, rate limiting
2. **Performance** — memoization, N+1 queries, polling vs realtime, duplicate listeners
3. **Code Quality** — duplicate files, linter disables, TODOs, stubs, dead code
4. **Test Coverage** — untested modules, skipped tests, test quality
5. **Output** — one summary table: Found / Fixed / Remaining

**Key behavior:** Unlike a human code review, `/code-review` is told to **fix issues directly**, not document them. It's a cleanup pass, not a checklist generator.

**When to run:**
- After `/implement` but before `/commit`
- On a codebase you inherited, to see what you're working with
- After a fast-and-loose prototype, to harden it

**When NOT to run:**
- During active feature work — the fixes create churn while you're still writing
- On code you're mid-refactor of — it'll "fix" things you're about to change

**Output format:**
```
| Category       | Found | Fixed | Remaining |
|----------------|-------|-------|-----------|
| Security       |     3 |     3 |         0 |
| Performance    |     2 |     1 |         1 |
| Code Quality   |     7 |     7 |         0 |
| Test Coverage  |     4 |     2 |         2 |
```

The "Remaining" column is your followup list. If everything is zero, you're done.

---

## `/security-audit` — security-only deep dive

**Starter kit:** YES
**Scope:** personal

A narrower variant of `/code-review` that runs **only** the Security phase but goes deeper:
- OWASP Top 10 checklist
- Dependency vulnerability scan (`npm audit`, `pip-audit`, etc.)
- Environment variable audit
- CSRF / SameSite cookie audit
- Content Security Policy check

Run before deploys. Run after adding authentication. Run when a CVE comes out for a dependency you use.

Not in the starter kit because for most projects, `/code-review`'s Phase 1 is enough. Add `/security-audit` when you have a security-sensitive project (auth, payments, health data).

---

## `/secrets-scan` — gitleaks-style secret detection

**Starter kit:** YES
**Scope:** personal

Scans the repo — not just the working tree — for hardcoded secrets. Looks at:
- Committed files in the current branch
- Git history (last N commits)
- `.env`-like files that shouldn't be tracked

Distinct from `/security-audit` because it's **history-aware**. A secret you committed 50 commits ago and later removed is still in the history and still a leak — `/secrets-scan` catches that.

**When to run:**
- Before making a private repo public
- After a "whoops I committed that" panic
- As a pre-flight check before pushing to a new remote

**Recovery path** if it finds something:
1. Rotate the secret (the one in history is burned — change it at the source)
2. Scrub from history with `git-filter-repo --replace-text`
3. Force push (dangerous — coordinate with anyone else on the branch)
4. Never allowlist the finding in `.gitleaks.toml` — that's how leaks survive cleanups

---

## `/audit` — organizational/governance audit

**Starter kit:** YES
**Scope:** personal

Generates a structured audit document for a topic, with the standard sections: Executive Summary, Findings, Recommendations, Action Items. Used as the **deliverable** form of an audit — not the investigation, but the report after the investigation.

**When to use:**
- A quality phase finished and you need a writeup for stakeholders
- A council member needs to file a formal audit (Chapter 05 governance flow)
- You want a template-driven audit instead of a free-form report

**Distinct from `/code-review`** which fixes issues directly. `/audit` only documents.

---

## The quality cadence

```
/implement          # write the code
/code-review        # clean up what you just wrote
/test               # confirm everything green
/commit             # land the change
```

Four commands, one fluid motion. Do this every time you finish a feature and you'll never ship broken code by accident.

---

## Related

- [testing.md](testing.md) — the test-running commands, which `/code-review` calls in Phase 4
- [git.md](git.md) — `/commit` and `/ship`
- [`principles/secrets-never-committed.md`](../../principles/secrets-never-committed.md) — the underlying secrets rule
