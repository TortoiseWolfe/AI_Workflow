# Principle — Five-File Components

> **Rule:** Every reusable React component is scaffolded as 5 files: an index, the implementation, a unit test, a Storybook story, and an accessibility test. Always. From day one.

---

## Why

### The war story

Early version of ScriptHammer had a `<Button>` component. Single file: `Button.tsx`. ~50 lines. "Tests can come later," the dev thought.

Six months in, ScriptHammer had 60 components. About 15 had tests. About 8 had Storybook stories. Zero had accessibility tests. The component library was technically a "library" but practically it was a heap of files where the test coverage and visual documentation depended entirely on whether the original author had remembered to add them.

A WCAG audit was scheduled. The auditor needed accessibility evidence for every interactive component. The dev had to:

1. Add accessibility tests to 60 components retroactively
2. Add Storybook stories to 52 components retroactively
3. Add unit tests to 45 components retroactively

**Total effort: 3 weeks of work that should have been spread across 6 months.**

Worse: many of the retroactive tests revealed bugs that had been shipping for months. The button component had a missing `aria-label` on icon-only variants. The modal didn't trap focus. The dropdown didn't announce its expanded state to screen readers. **Every one of these would have been caught at component-creation time** if the accessibility test had been required from day one.

The dev formalized the rule: **5 files, scaffolded by `pnpm run generate:component`, no exceptions**. Every new component gets all 5 files at the moment of creation. Empty stub tests are fine — the structure is what matters. The structure is what makes the discipline survive when you're tired or rushed.

The next 60 components were created with all 5 files. Coverage stayed at 100%. The next WCAG audit took 4 hours instead of 3 weeks.

### The general principle

There are two ways to maintain test coverage:

1. **Discipline** — every new file gets tests because the dev cares enough to write them
2. **Structure** — every new component is scaffolded with stubs that physically exist; the dev fills them in

Discipline fails. Always. Not because devs are lazy — because some weeks you're under deadline, some commits are emergency fixes, and "I'll add tests later" becomes "tests don't exist."

Structure works because the cost of *not* writing a test is now visible. An empty `Button.test.tsx` file with one TODO comment is a screaming reminder. A missing `Button.test.tsx` file is invisible.

The 5-file pattern is structure. The scaffolder generates all 5 files. You can leave one empty for now, but you can't leave it missing — and the next person to read the component sees the empty stub and fills it in.

---

## The 5 files

```
src/components/Button/
├── index.tsx                       # Barrel export — `export { Button } from './Button'`
├── Button.tsx                      # Implementation
├── Button.test.tsx                 # Unit test (Vitest + RTL)
├── Button.stories.tsx              # Storybook story
└── Button.accessibility.test.tsx   # Pa11y / axe test
```

| File | Purpose | Why |
|---|---|---|
| `index.tsx` | Barrel export | Lets consumers import from `'@/components/Button'` instead of `'@/components/Button/Button'`. Decouples implementation file naming from import path. |
| `Button.tsx` | The component itself | Where the real work lives. Props, JSX, logic. |
| `Button.test.tsx` | Unit test | Tests behavior in isolation. Mocks dependencies. Fast. |
| `Button.stories.tsx` | Storybook story | Visual documentation + manual QA. Multiple variants per story file. |
| `Button.accessibility.test.tsx` | A11y test | Pa11y or axe-core test. Validates ARIA, keyboard nav, contrast, focus management. |

5 files. 1 component. Always.

---

## How to apply

### The scaffolder

ScriptHammer, TurtleWolfe, and SpokeToWork all have a `pnpm run generate:component` script that creates the 5 files from a template:

```bash
docker compose exec scripthammer pnpm run generate:component Button
```

This creates `src/components/Button/` with all 5 files, each filled with a starter template specific to its file type. The dev fills in the implementation; the structure is given.

If your project doesn't have a generator yet, **write one before you write your second component**. The 5-file pattern only works if the friction of creating all 5 is less than the friction of "I'll add the others later."

### Template content

Each scaffolded file should have **just enough** to be useful:

- **`index.tsx`**: one line, the barrel export
- **`Button.tsx`**: a stub component that takes `children` and renders a button
- **`Button.test.tsx`**: one passing test (e.g., `it('renders children', () => { ... })`)
- **`Button.stories.tsx`**: one default story with the basic variant
- **`Button.accessibility.test.tsx`**: one Pa11y test that runs against the default variant

The dev replaces these stubs with real content. The test file is never empty. The story file is never missing. The structure is the discipline.

### When to break the rule

There are real exceptions:

- **Page components** (`src/app/page.tsx`) — these are routes, not reusable components. They get tested via E2E (`tests/e2e/`), not unit tests in their own directory.
- **Layout components** that are pure structural wrappers (no logic, no props) — sometimes the test is "does it render its children?" which is trivial. Acceptable to skip.
- **Server components** that don't render anything visual — accessibility test makes no sense. Skip the a11y file.
- **Single-use private helpers** that aren't real components — these don't go in `src/components/` at all; they live next to the file that uses them.

Any other exception is suspicious. Default to all 5 files.

### Beyond React

The principle generalizes:

- **Vue/Svelte/Angular** — same idea, adjust file names for the framework
- **Backend services** — every service gets `Service.ts` + `Service.test.ts` + `Service.integration.test.ts` (no Storybook, no a11y, but still 3 files instead of 1)
- **Python modules** — `module.py` + `test_module.py` + `test_module_integration.py`
- **Go packages** — every public function gets a `_test.go` file at minimum

The point is: **never let a single-file unit exist when a multi-file scaffold would have caught the missing tests at creation time.**

---

## What this principle does NOT mean

- **It doesn't mean every component is reusable.** Some components are page-specific. They still get the 5 files.
- **It doesn't mean tests must be exhaustive on day one.** A passing stub test is fine. The point is the file *exists*. You'll fill it in.
- **It doesn't mean Storybook is mandatory at runtime.** You can run the project without Storybook — it's a separate dev server. But the story file lives in version control regardless.
- **It doesn't mean a 5-line button needs a 100-line test file.** Match the test to the complexity. A trivial component gets a trivial test.

---

## Related

- ScriptHammer's `pnpm run generate:component` — the reference implementation
- [`02-give-it-context/writing-claude-md.md`](../02-give-it-context/writing-claude-md.md) — telling Claude about the pattern via `CLAUDE.md`
- [`04-the-speckit-loop/walkthrough.md`](../04-the-speckit-loop/walkthrough.md) — see how `/speckit.plan` enforces the pattern in the file layout
