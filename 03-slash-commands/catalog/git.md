# Command Catalog — Git

Commands that interact with git. Claude Code can run any `git` command raw, but these wrappers enforce the workflow rules every commit has to follow: Docker-first quality checks, conventional commits, Claude Code footer, no surprise pushes.

---

## `/commit` — the disciplined commit

**Starter kit:** YES
**Scope:** personal
**File:** [`../starter-kit/.claude/commands/commit.md`](../starter-kit/.claude/commands/commit.md)

Runs a strict commit sequence:

1. **Lint** inside Docker. Fails → stop.
2. **Type-check** inside Docker (if the project has one). Fails → stop.
3. **Stage changes.** Shows `git status`, asks user which files to include (default: all).
4. **Generate a conventional commit message** from the staged diff.
5. **Commit** with the Claude Code co-author footer.
6. **Report** the hash and subject.
7. **Does NOT push.** Explicit user action required.

### Conventional commit types

| Prefix | Meaning |
|---|---|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation changes |
| `style:` | Formatting only, no logic |
| `refactor:` | Code restructure without behavior change |
| `test:` | Test additions or changes |
| `chore:` | Build/tooling/dependency changes |

Subjects under 72 characters. Body only if the change needs context.

### The footer

Every commit includes:

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Why the footer matters:**
- Honest attribution — Claude contributed to this commit, mark it
- Searchable — `git log --grep "Co-Authored-By: Claude"` shows every AI-assisted commit
- Team consistency — when teammates also use Claude Code, everyone's commits look the same

### What `/commit` refuses to do

- **Commit with failing lint or type-check.** The Whole Point™ of `/commit` vs raw `git commit` is that quality checks are pre-flight, not post-flight.
- **Push.** Explicit user action only. One command, one concern.
- **Amend previous commits.** Unless you ask. Amending is destructive.
- **Use `--no-verify`.** Ever. If a pre-commit hook fails, fix the underlying issue.

---

## `/ship` — commit + merge + cleanup

**Starter kit:** YES
**Scope:** personal
**File:** [`../starter-kit/.claude/commands/ship.md`](../starter-kit/.claude/commands/ship.md)

The "I'm done with this feature branch" command. Runs:

1. **Pre-flight checks** — branch state, quality checks (same as `/commit`)
2. **Commit** any outstanding changes (same as `/commit`)
3. **Switch to main**
4. **Merge** the feature branch with `--no-ff` (preserves the branch topology)
5. **Delete the feature branch** (local only)
6. **Cleanup** — lists stray local branches, offers to delete each one
7. **Final report** — hash, merge confirmation, remaining branches
8. **Does NOT push.** Still your call.

### When to use `/ship` vs `/commit`

| Situation | Use |
|---|---|
| Mid-feature work, landing a partial step | `/commit` |
| Feature is done, ready for main | `/ship` |
| You've been working on main directly (don't, but if) | `/commit` (there's no merge) |
| You want to just get the commit in without touching branches | `/commit` |

`/ship` is `/commit` followed by the branch dance. If you're not ready to merge, don't use `/ship`.

### What `/ship` won't do

- **Push.** Still your call.
- **Resolve merge conflicts.** If the merge has conflicts, `/ship` stops and hands you the conflicted files.
- **Delete an unmerged branch.** Uses `git branch -d`, not `-D`. If the branch isn't merged, deletion fails — which is what you want.

---

## Why not raw `git` commands?

You *can* ask Claude to run raw `git commit -am "fix stuff"`. Claude will do it. But:

- You'll forget lint and type-check
- You'll write "fix stuff" as the message
- You'll forget the footer
- Eventually you'll amend-and-force-push and lose work

`/commit` enforces the rules. Use it.

### Exception: interactive rebases, cherry-picks, reflog rescue

`/commit` and `/ship` don't cover advanced git. For:
- `git rebase -i` (interactive rebase)
- `git cherry-pick`
- `git reflog` for accident recovery
- `git bisect`

…run raw commands. These are situational and not worth wrapping.

---

## The golden path

```
# edit files via Claude, test changes with /test
/commit                 # land the change
# ... maybe more commits ...
/ship                   # merge to main when feature is done
git push                # explicit — you decide when
```

Four operations in sequence. Never skip `/commit`'s lint step. Never force-push main. Never ask `/ship` to do things it refuses.

---

## Related

- [quality.md](quality.md) — `/code-review` before `/commit` catches more than lint
- [testing.md](testing.md) — `/test` verifies the suite before you ship
- [`principles/docker-first.md`](../../principles/docker-first.md) — why the checks run inside the container
