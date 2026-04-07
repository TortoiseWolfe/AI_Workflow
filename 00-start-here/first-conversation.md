# Your First Conversation

A 5-minute primer on what to expect when you talk to Claude Code, and the three things you need to know to keep from fighting it.

---

## 1. Claude thinks before speaking

When you type a message and press Enter, Claude does not respond instantly. With `alwaysThinkingEnabled: true` (set in [Chapter 00](README.md#the-four-line-settingsjson)), there's a reasoning phase before the response. You'll see a "thinking" indicator. This is normal. Do not interrupt it.

**Rule of thumb:** If the thinking indicator has been running for more than 60 seconds on a simple request, you probably asked something too vague. Press `Esc` to interrupt, rephrase, and try again.

## 2. Tool calls require permission

Claude Code edits files, runs shell commands, and searches your codebase. Each of those is a "tool call." By default, Claude asks permission before running a tool. You'll see something like:

```
Claude wants to use: Bash
Command: docker compose exec spoketowork pnpm run lint
Approve?  [y/n/always]
```

- `y` — approve this one call
- `n` — deny it; Claude will adjust
- `always` — approve this exact command forever (dangerous for destructive commands — don't `always` a `git push --force`)

**The three buttons:**

| Button | When to use |
|---|---|
| `y` | Normal flow. 95% of clicks. |
| `n` | Claude is about to do the wrong thing. Deny and explain why. |
| `always` | Only for safe, repetitive commands (`git status`, `ls`, `docker compose exec ... pnpm test`). Never for deletes, pushes, or network calls. |

## 3. `/clear` is your friend, `/compact` is your enemy

When your conversation gets long, context starts to fill up. You have two options for making room:

- **`/clear`** — wipes the entire conversation and starts fresh. Cheap, fast, clean.
- **`/compact`** — summarizes the conversation and keeps the summary. Sounds great; it's a trap. Compacted context is *poisoned* — old mistakes, wrong turns, and outdated file contents get preserved as "facts" Claude now believes. Bugs from compacted sessions are maddening to debug.

**Rule:** When context is full, run `/clear` then re-prime with `/prep` (you'll learn this in [Chapter 02](../02-give-it-context/)). Don't reach for `/compact` unless you have a very specific reason.

> **Why this rule exists:** TurtleWolfe's war story. Chapter 02's `priming-patterns.md` has the longer version. TL;DR: a compacted session once kept a "the test file is at path X" summary after the file moved. Claude wrote three wrong patches in a row looking for a file that didn't exist. `/clear` + `/prep` would have caught it in one message.

---

## 4. How to read Claude's output

Claude Code writes in GitHub-flavored markdown. When it mentions a file, it uses the format:

```
src/components/Button/Button.tsx:42
```

That's a clickable jump (file:line) in most terminals. Click it, land in the right spot.

When Claude proposes a diff, it shows the edit *before* applying it. Read the diff. If it looks wrong, say "no, instead do X." Claude will revise.

## 5. When to interrupt

Press `Esc` to interrupt any time you see Claude going sideways. You are not being rude. Interrupting early saves tokens and time. Do not let Claude finish writing 300 lines of the wrong thing because you were too polite to stop it.

**Interrupt when:**
- Claude starts editing a file you didn't mean to touch
- Claude is about to run a destructive command
- Claude is thinking for longer than the task warrants
- You realize mid-response that you asked the wrong question

**Don't interrupt when:**
- Claude is in the middle of a tool call (let it finish, then correct)
- You're just impatient — give thinking mode its 20-30 seconds

---

## You're ready

That's the whole primer. `/help`, `y/n/always`, `/clear` not `/compact`, click file:line, interrupt early.

**Next:** [Chapter 01 — Bootstrap a Repo](../01-bootstrap-a-repo/)
