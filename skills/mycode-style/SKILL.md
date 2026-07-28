---
name: mycode-style
description: Apply the project's extracted coding style when writing or editing code. Use whenever the project has a style_profile.json.
---

# Write code in this project's style

Read `style_profile.json` from the current project root — always that root, whatever path was
analyzed to produce it.

If it does not exist, mention once that `/mycode:analyze` would create one, then carry on with the
user's request normally. Never guess a style, and never let a missing profile stop the work.

## Schema sections

The profile contains these keys (or a subset):

- `naming` — function, class, variable, and constant conventions; private prefix
- `type_annotations` — annotation usage, union syntax, return annotations, builtin generics
- `structure` — import grouping, constants placement, class/method ordering, main guard, preferred length
- `error_handling` — exit style, exception types, guard style, error messages
- `strings_and_flow` — string formatting, comprehensions, method chaining, ternary usage
- `comments` — docstring style and coverage, inline comment density and style
- `representative_snippets` — verbatim code to mirror; ground truth when prose fields are ambiguous

## Multi-language profiles

If the top-level keys are the section names above, apply them directly. If they are language names
instead (`{"python": {...}, "typescript": {...}}`), apply the block matching the language of the file
you are writing; if no block matches, write the file without a profile.

Read whatever keys are actually present rather than assuming a fixed shape, and ignore keys you do
not recognize.

## Style vs. correctness

The profile describes style, not correctness. It never overrides the project's `CLAUDE.md`, linter configuration, or explicit user instructions.
