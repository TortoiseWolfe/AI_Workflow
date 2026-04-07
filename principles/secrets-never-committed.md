# Principle — Secrets Never Committed

> **Rule:** No secret, token, key, or credential may appear as a literal value in any file committed to git. All secrets live in `.env` (gitignored). Committed files use `${VAR:-inert-placeholder}` patterns.

---

## Why

### The war story

A SpokeToWork dev (early version, before the rule was formal) added Supabase to local dev. Supabase generates JWT tokens for the anon key and service role key. To make local dev work, the dev hardcoded the JWTs into `docker-compose.yml`:

```yaml
SUPABASE_ANON_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

"They're just demo JWTs," the thinking went. "They only work against the local Supabase stack."

The dev pushed. The repo was public.

GitHub's secret scanner flagged the JWTs within minutes. They got an automated email. They thought "oh, false positive, they're demo keys" and ignored it.

**The actual problem:**
1. The JWT format is the JWT format. Even local-only JWTs are *valid credentials* against the `service_role` of any Supabase instance that uses the same `JWT_SECRET`. If anyone knew the team's `JWT_SECRET` (which was *also* hardcoded — that was the next find), they could mint their own service_role tokens for any production Supabase instance using the same secret.
2. The JWTs were now in git history forever. Even removing them from the latest commit didn't help.
3. To actually clean up, the dev had to:
   - Rotate the JWT_SECRET in the Supabase project
   - Rotate every service that depended on those tokens
   - Use `git-filter-repo --replace-text` to scrub history
   - Force-push (which broke every fork and CI build referencing those commits)
   - Coordinate with everyone who had cloned to re-clone

**Total cost: 6 hours of cleanup, plus an awkward Slack message to the team explaining what happened.**

The fix that should have been there from the start, in `docker-compose.yml`:

```yaml
SUPABASE_ANON_KEY: ${SUPABASE_LOCAL_ANON_KEY:-set-anon-key-in-env-file}
SUPABASE_SERVICE_ROLE_KEY: ${SUPABASE_LOCAL_SERVICE_ROLE_KEY:-set-service-role-in-env-file}
```

The real values live in `.env` (gitignored). The committed file shows the variable name. Inert placeholder if not set. Zero secrets in git.

### The general principle

There are two truths about secrets:

1. **You cannot un-leak a secret.** Once a credential is in git history (or in a public log, or in a screenshot), it's burned. Rotate it. Don't allowlist it. Don't pretend it's "just for dev."

2. **The cost of preventing leaks is near zero. The cost of cleaning them up is high.** A `${VAR:-placeholder}` pattern takes 5 seconds to write. A `git-filter-repo` scrub takes hours and breaks everyone's local clones.

The math is overwhelming. Make the cheap habit. Skip the expensive cleanup.

---

## How to apply

### The rules

1. **All secrets go in `.env`.** Always. No exceptions.
2. **`.env` is gitignored.** Always. No exceptions.
3. **`.env.example` is committed** and shows variable names with empty or inert values.
4. **Committed files reference variables**, never literal values:
   ```yaml
   # CORRECT
   API_KEY: ${API_KEY:-set-in-env-file}

   # WRONG
   API_KEY: sk_live_a1b2c3d4e5f6...
   ```
5. **Inert placeholders are okay.** `${API_KEY:-set-in-env-file}` is fine. The placeholder is not a real key — it's a string that fails informatively if the env var is missing.
6. **Never allowlist a secret in `.gitleaks.toml`.** Not in `regexes`, not in `commits`, not anywhere. If gitleaks flags a real secret, the fix is to remove the secret, not to suppress the warning.
7. **What counts as a secret:**
   - API keys, tokens, passwords (obvious)
   - JWTs (even "demo" JWTs — they are valid credentials)
   - OAuth client IDs and secrets
   - `SECRET_KEY_BASE`, `JWT_SECRET`, webhook secrets
   - GitHub PATs, deployment tokens
   - Database passwords (even local ones if they share with prod)
8. **If a secret leaks into git history**, scrub it with `git-filter-repo --replace-text` and force push. Rotate the leaked secret. Notify the team.

### The pattern

```bash
# .env (gitignored)
API_KEY=sk_live_a1b2c3d4e5f6
DATABASE_URL=postgres://user:realpassword@db:5432/dev
JWT_SECRET=long-random-string-32-chars-min

# .env.example (committed, shows variable names only)
API_KEY=set-in-local-env
DATABASE_URL=postgres://user:change-me-local-password@db:5432/dev
JWT_SECRET=change-me-long-random-string

# docker-compose.yml (committed)
services:
  app:
    environment:
      API_KEY: ${API_KEY:-set-in-local-env}
      DATABASE_URL: ${DATABASE_URL:-postgres://user:change-me-local-password@db:5432/dev}
      JWT_SECRET: ${JWT_SECRET:-change-me-long-random-string}
```

Three files. Two committed, one gitignored. No secrets in version control. Ever.

### Tooling

- **gitleaks** — pre-commit hook scans staged files for secret-like patterns
- **`/secrets-scan` slash command** — manual sweep of the working tree and history
- **GitHub secret scanning** — auto-scans pushed code for known secret formats
- **Pre-commit hook** in your `.husky/` or `.git/hooks/pre-commit` that runs gitleaks before allowing the commit

### What to do if a secret leaks

1. **Rotate the leaked secret immediately.** Don't wait. The cleanup of git history is secondary to the actual security action.
2. **Find every place the secret was used.** Update them to the new value via `.env`.
3. **Scrub git history** with `git-filter-repo --replace-text`:
   ```bash
   echo "old-secret-value==>REDACTED" > replacements.txt
   git filter-repo --replace-text replacements.txt
   git push --force-with-lease
   ```
4. **Notify the team.** Anyone with a clone needs to re-clone or rebase carefully.
5. **Update `CLAUDE.md`** with the lesson if it wasn't already explicit enough to prevent it.

---

## Related

- [`docker-first.md`](docker-first.md) — sibling mandatory rule
- [`01-bootstrap-a-repo/templates/env.example.template`](../01-bootstrap-a-repo/templates/env.example.template) — the starter template
- [`03-slash-commands/catalog/quality.md`](../03-slash-commands/catalog/quality.md) — `/secrets-scan`
- The full SpokeToWork `CLAUDE.md` Secrets section is the canonical reference
