# When This Actually Helps

Honest assessment of when the 27-terminal assembly line is worth setting up vs when it's just complexity for its own sake. **Read this before reading the rest of Chapter 05.** It will save you time.

---

## The honest truth

The assembly line is **TurtleWolfe's personal workflow** for production projects with high coordination requirements. It's not a generic best practice. It's not even the right answer for most projects.

For most TSD interns, **most of the time, on most projects**, the right answer is:

1. Chapter 04's SpecKit loop
2. Plus a custom slash command or two from Chapter 03's exercise
3. That's it

Don't reach for Chapter 05 because it looks impressive. Reach for it when you have a specific problem that the SpecKit loop can't solve.

---

## Use the assembly line when…

### 1. You have genuinely parallelizable work that doesn't share state

Example: generating 12 wireframes for a feature where each wireframe is independent. The SpecKit loop generates them sequentially; the assembly line generates 3 in parallel via Generator1/2/3.

**Test:** Can the work be split such that worker A's output doesn't depend on worker B's output? If yes, parallelism wins. If no, sequential is fine.

### 2. You have audit / governance requirements that need formal processes

Example: a financial services project where every architectural decision needs a council vote and an audit trail. The RFC + council infrastructure exists for exactly this.

**Test:** Does someone outside the dev team need to see decision provenance? If yes, the RFC system pays for itself. If no, just document decisions in the spec.

### 3. You're running a multi-day or multi-week feature with distinct phases

Example: a 3-week build where weeks 1-2 are wireframes, week 3 is implementation, and the QA pass is its own week. The phases naturally map to assembly line stages.

**Test:** Are there clear, slow phases with handoffs? If yes, the assembly line's role-based isolation helps. If the work is one continuous coding session, just code.

### 4. You're juggling multiple features in parallel

Example: 4 features in flight at once, each in different phases. The assembly line lets you have a "Generator currently working on feature 5" and "Developer currently coding feature 3" running side by side without interfering.

**Test:** Are you context-switching between features daily? If yes, separate terminals reduce mental overhead. If you're only working on one feature at a time, single Claude works fine.

### 5. The cost of being wrong is high enough to justify ceremony

Example: a security-critical change in a regulated industry. You want Security, Architect, and CTO to independently review before code is written. The RFC + voting flow forces that.

**Test:** Would a one-person mistake cost more than the assembly line's setup time? If yes, ceremony pays. If you're prototyping a UI nobody will see, skip it.

---

## DON'T use the assembly line when…

### 1. You're a solo dev on a side project

You're the only person who would ever read an RFC. You're the only voter. You're the only worker. The assembly line is overhead with no benefit.

### 2. The project is small or short-lived

If the project will exist for less than a month, the setup time for the assembly line is more than the time you'd save running it.

### 3. You haven't mastered Chapter 04 yet

The SpecKit loop is the foundation. If you're still figuring out when to run `/speckit.clarify`, don't add 27 terminals on top of that.

### 4. You don't have the supporting infrastructure

The assembly line needs:
- `validate-wireframe.py` (or equivalent for your domain)
- `.claude/roles/` with 27 role files
- `scripts/tmux-session.sh` and `scripts/tmux-dispatch.sh`
- `.terminal-status.json` schema agreement
- `docs/interoffice/` directory tree

If you don't have these, the assembly line doesn't run. Setting them up is days of work, not hours.

### 5. You're firefighting

The assembly line is for *planned* work with discrete phases. If production is on fire and you need to ship a hotfix in 30 minutes, single Claude + `/commit` is faster.

### 6. The team is one person

The assembly line is a way to organize a *team* of AI workers. If there's only one human in the loop, the bottleneck is the human, not the workers — adding more workers doesn't help.

---

## The graduation path

Most TSD interns should go through this progression:

1. **Week 1-2:** Chapters 00-03. Daily slash commands, no SpecKit yet. Get fluent in `/prep`, `/commit`, `/test`, `/code-review`.

2. **Week 3-4:** Chapter 04. SpecKit loop on small features. Get comfortable with `/speckit.specify` through `/speckit.implement`.

3. **Months 2-3:** SpecKit loop on bigger features. Add custom slash commands as you notice repetition.

4. **Month 4+:** Read Chapter 05 once. Understand it conceptually. Don't try to set it up yet.

5. **Month 6+:** If you hit a project that genuinely needs parallel wireframes or council governance, set up Chapter 05 carefully, one piece at a time. Start with `install-full-kit.sh`, then `dispatch.md` and `queue.md`, then add roles incrementally.

6. **Year 1+:** Maybe you're running the full 27-terminal assembly line on a real project. Maybe you're not. Both are fine.

The point isn't to climb to Chapter 05. The point is to know when each tool earns its complexity.

---

## What you should DEFINITELY learn from Chapter 05 even if you never use it

Even if you never run the assembly line, Chapter 05 teaches concepts worth knowing:

1. **Role-based context isolation.** The idea that different terminals can have different primers (`/prime developer` vs `/prime architect`) generalizes — even if you never run 27 terminals, you can run 2 with different contexts.

2. **Queue-driven work.** The `.terminal-status.json` queue is a pattern. You can adopt the pattern without the full assembly line — just keep a `tasks.md` you check off.

3. **The Operator/Worker distinction.** Knowing that an orchestrator should *only* dispatch and never *do* helps you avoid mixing layers in your own scripts.

4. **The RFC pattern.** Even solo, writing an "RFC for myself" before a major change forces you to think through alternatives. The format (Summary / Motivation / Proposal / Alternatives / Impact) is gold.

5. **`tmux send-keys ... Enter` will save you a week.** Even one-off tmux scripts benefit from knowing this.

---

## The bottom line

> **Chapter 05 is the signature move. The signature move is not the daily move.**

Chapter 04 is the daily move. Master it first. Read Chapter 05 to know what's possible. Set it up only when a real project demands it.

---

## Related

- [README.md](README.md) — chapter overview
- [the-assembly-line.md](the-assembly-line.md) — what you'd be setting up
- [the-operator.md](the-operator.md) — the meta-terminal that drives everything
- Chapter 04 — the SpecKit loop, which is what you should actually use 95% of the time
