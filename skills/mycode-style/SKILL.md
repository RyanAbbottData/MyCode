---
name: mycode-style
description: Apply the project's extracted coding style when writing or editing Python. Use whenever the project has a style_profile.json.
---

# Write code in this project's style

Read `style_profile.json` from the project root.

If it does not exist, tell the user to generate one first — either the `analyze_codebase` MCP tool
from this plugin, or `my-code analyze .` — and stop. Do not guess a style.

Follow the profile when writing or editing code:

- `naming` — identifier conventions for functions, classes, variables, and constants
- `structure` — import ordering, module layout, class/method ordering, preferred length
- `comments` — docstring style and inline comment density
- `representative_snippets` — mirror this formatting verbatim; it is the ground truth when the
  prose fields are ambiguous

The profile schema varies by which backend produced it. Read whatever keys are actually present
rather than assuming a fixed shape, and ignore keys you do not recognize.

The profile describes style, not correctness. It never overrides a project's `CLAUDE.md`, its
linter configuration, or an explicit instruction from the user.
