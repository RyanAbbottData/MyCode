```
 __  __        ____          _
|  \/  |_   _ / ___|___   __| | ___
| |\/| | | | | |   / _ \ / _` |/ _ \
| |  | | |_| | |__| (_) | (_| |  __/
|_|  |_|\__, |\____\___/ \__,_|\___|
        |___/
```

> **Style-aware code generation for Claude Code.** Analyze a codebase to extract its coding style, then write new code that matches it.

---

## What it does

MyCode is a [Claude Code](https://claude.com/claude-code) plugin. It reads a sample of your codebase and records how you write code — naming conventions, type annotation style, import grouping, docstring format, error handling patterns. Claude then uses that record to write new code that matches your style.

MyCode does not read every file in your repository. It samples entry points, your largest or most complex modules, and a few simple files, then builds a profile from that sample. This keeps analysis fast even on large repositories.

All of the work happens inside Claude Code itself. There is no separate program to run and no other system to maintain.

---

## Install

Add this repository as a plugin marketplace, then install the plugin:

```
/plugin marketplace add RyanAbbottData/MyCode
/plugin install mycode@mycode
```

That is the entire setup. You do not need to install any package. You do not need an API key. You do not need to start a server.

To develop against a local checkout of this repository instead of the marketplace, run:

```
claude --plugin-dir /path/to/MyCode
```

---

## What you get

| Name | Type | Purpose |
|------|------|---------|
| `/mycode:analyze` | Command | Analyzes a directory and writes `style_profile.json` |
| `mycode-style` | Skill | Reads `style_profile.json` and applies it when Claude writes code |

---

## Usage

1. **Analyze your codebase once.** Run `/mycode:analyze` (optionally with a path). Claude samples the source files and writes `style_profile.json` to the project root.
2. **Ask for code as you normally would.** The `mycode-style` skill fires on its own. It reads `style_profile.json` and applies your conventions before Claude writes anything. If no profile exists yet, the skill mentions `/mycode:analyze` once and continues with your request — it never blocks the request.
3. **Commit `style_profile.json`.** This lets your whole team share the same style profile.

---

## What the profile captures

`style_profile.json` has up to seven sections. Each section describes one part of your coding style.

| Section | What it governs |
|---------|------------------|
| `naming` | Function, class, variable, and constant naming patterns; private-member prefix |
| `type_annotations` | How often types are used; union syntax; return annotations; generic type style (omitted for languages that have no type system) |
| `structure` | Import grouping; where constants live; class and method order; main-guard usage; preferred file and line length |
| `error_handling` | How programs exit; common exception types; error-prevention style; error message format |
| `strings_and_flow` | String formatting; comprehension usage; method chaining; ternary usage |
| `comments` | Docstring style and coverage; inline comment density and style |
| `representative_snippets` | Verbatim code samples that show the style in practice |

When the prose fields above are ambiguous, `representative_snippets` is the ground truth — Claude copies its patterns directly.

For a multi-language repository, these sections sit under a language key, for example `{"python": {...}, "typescript": {...}}`. For a single-language repository, the sections sit at the top level.

The profile describes **style, not correctness**. It never overrides your project's `CLAUDE.md`, your linter configuration, or an explicit instruction in your prompt.

---

## Troubleshooting

| Symptom | Cause and fix |
|---------|----------------|
| `mycode` does not appear in `/plugin` | The plugin install did not complete. Run `/plugin install mycode@mycode` again. |
| The `mycode-style` skill never fires | No `style_profile.json` exists in the project root yet. Run `/mycode:analyze` first. |
| Generated code ignores the profile | An explicit instruction in your prompt, or your project's `CLAUDE.md`, takes precedence by design. |

---

## Previously a Python library

MyCode was previously distributed as a Python package, `mycode-aiagent` on PyPI. That package is discontinued as of version 0.7.0 and is unrelated to this plugin — you do not need to `pip install` anything. This plugin replaces it in full and needs none of the old package, its API keys, or its server.
