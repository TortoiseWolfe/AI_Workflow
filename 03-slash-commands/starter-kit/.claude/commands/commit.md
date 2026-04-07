---
description: Run linter, type-check, and commit changes with a descriptive message
scope: personal
---

Commit code changes after verifying quality checks pass.

## Docker-First Requirement

**CRITICAL:** If the project has a `docker-compose.yml` or `CLAUDE.md` mentioning Docker-first development:
- ALL commands (git, pnpm, npm) MUST run through Docker
- Use `docker compose exec <service> <command>` for everything
- Check if the container is running; if not, run `docker compose up -d` first

## Instructions

### 1. Run Quality Checks

Detect the package manager and service name from `docker-compose.yml` and `package.json`. Then:

- Execute lint: `docker compose exec <service> <pm> run lint`
- Execute type-check (if the project has one): `docker compose exec <service> <pm> run type-check`
- If either fails, stop and report the errors. Do not commit.

### 2. Stage and Commit

- Run `git status` to see all uncommitted changes (staged, unstaged, untracked)
- If there are changes, show the user the full list and ask which to include
- Default: everything gets committed unless the user says otherwise
- Stage confirmed files with `git add` (through Docker if Docker-first)
- Run `git diff --cached --stat` to summarize staged changes
- If there are no changes to commit, report that and stop

### 3. Create the Commit Message

Analyze the staged changes and draft a commit message following conventional commits:

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation changes
- `style:` — formatting, no code change
- `refactor:` — code refactor
- `test:` — test changes
- `chore:` — build/tooling changes

Keep the subject under 72 characters. Include a body only if the change needs context.

**Always include this footer:**

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 4. Commit

Pass the message via HEREDOC to preserve formatting:

```bash
git commit -m "$(cat <<'EOF'
feat: add landing page personalization

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### 5. Report

- Show the commit hash and subject line
- Note that changes are local only — run `git push` to push to remote
- Do NOT push automatically

## Rules

- **Only commit if all quality checks pass.** Never commit broken code.
- **Never push unless explicitly asked.** This command commits locally.
- **Never amend previous commits** unless explicitly asked.
- **Never use `--no-verify`** to skip hooks. If a hook fails, fix the underlying issue.
