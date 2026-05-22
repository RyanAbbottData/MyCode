```
 __  __        ____          _
|  \/  |_   _ / ___|___   __| | ___
| |\/| | | | | |   / _ \ / _` |/ _ \
| |  | | |_| | |__| (_) | (_| |  __/
|_|  |_|\__, |\____\___/ \__,_|\___|
        |___/
```

> **Style-aware code generation.** Analyze any codebase to extract its coding style, then generate new code that matches it exactly.

---

## What it does

MyCode learns how a developer or team writes code — naming conventions, type annotation style, import grouping, docstring format, error handling patterns — and uses that style profile to generate new code that feels like it was written by the same hand.

It is built to slot into larger agentic systems: the analyzer and generator are clean library functions, and the backend is swappable (local LLM, Claude, or OpenAI).

---

## Requirements

- Python 3.10+
- A running AI backend (see [Backends](#backends))

---

## Installation

```bash
# Clone and install in editable mode
git clone <repo-url>
cd MyCode
pip install -e .

# For Claude backend support
pip install -e ".[claude]"

# For OpenAI backend support
pip install -e ".[openai]"

# For all backends
pip install -e ".[all]"
```

The `my-code` CLI command is registered automatically on install.

---

## Backends

MyCode delegates inference to a pluggable backend. Choose one based on what you have available.

| Backend | Flag | Requirement |
|---|---|---|
| Local LLM via Ricky | `--backend llama` (default) | Ricky MCP server running at `localhost:8000` |
| Anthropic Claude | `--backend claude` | `ANTHROPIC_API_KEY` env var or `--api-key` |
| OpenAI | `--backend openai` | `OPENAI_API_KEY` env var or `--api-key` |
| Custom MCP server | `--backend mcp` | Any MCP server at `--mcp-url` |

### Starting the local LLM backend (Ricky)

```bash
# Windows
serve_llama.bat

# The Ricky MCP server must be running before using --backend llama
```

---

## CLI Usage

### Step 1 — Analyze a codebase

Point MyCode at any directory. It reads every `.py` file and builds a style profile.

```bash
my-code analyze ./path/to/codebase
```

With verbose output:
```bash
my-code analyze ./path/to/codebase --verbose
```

Using a different backend:
```bash
my-code --backend claude analyze ./path/to/codebase
my-code --backend openai --api-key sk-... analyze ./path/to/codebase
```

The profile is saved to `style_profile.json` by default. Specify a different path with `--profile`:
```bash
my-code analyze ./path/to/codebase --profile ./profiles/my_team.json
```

### Step 2 — Generate code

```bash
my-code generate "write a function that parses a CSV file and returns a list of dicts"
```

MyCode loads `style_profile.json` and instructs the backend to produce code that matches the analyzed style — naming, annotations, docstrings, structure and all.

```bash
# Use a specific profile
my-code generate "write a retry decorator" --profile ./profiles/my_team.json

# Use Claude to generate
my-code --backend claude generate "write a binary search function"

# Override the model
my-code --backend claude --model claude-sonnet-4-6 generate "write a rate limiter"
```

---

## CLI Reference

```
my-code [OPTIONS] COMMAND

Options:
  --backend {llama,claude,openai,mcp}   AI backend to use (default: llama)
  --api-key TEXT                         API key for claude/openai backends
  --model TEXT                           Override the default model
  --ricky-url TEXT                       Ricky MCP server URL (default: http://localhost:8000/mcp)
  --mcp-url TEXT                         Custom MCP server URL (default: http://localhost:8001/mcp)
  --profile TEXT                         Path to style profile JSON (default: style_profile.json)

Commands:
  analyze PATH    Analyze a codebase and write a style profile
    --verbose     Print each file as it is analyzed

  generate TASK   Generate code matching the saved style profile
```

---

## Python API

MyCode is a first-class library. All CLI functionality is available programmatically.

```python
from my_code import StyleAnalyzer, generate_code, make_backend
from pathlib import Path

# Create a backend
backend = make_backend()                          # local llama (default)
backend = make_backend("claude")                  # Claude (reads ANTHROPIC_API_KEY)
backend = make_backend("openai", api_key="sk-...") # OpenAI

# Analyze a codebase
analyzer = StyleAnalyzer(backend)
profile = analyzer.analyze_codebase(Path("./my_project"), verbose=True)

# Save and reload the profile
StyleAnalyzer.save_profile(profile, Path("style.json"))
profile = StyleAnalyzer.load_profile(Path("style.json"))

# Generate code
code = generate_code(
    task="write a function that validates an email address",
    backend=backend,
    profile=profile,
)
print(code)
```

### Bring your own backend

Implement `AIBackend` to connect any model:

```python
from my_code import AIBackend, StyleAnalyzer, generate_code

class MyBackend(AIBackend):
    max_file_chars = 4000  # how much of each file to send for analysis

    def ask_for_code(self, prompt: str) -> str:
        # call your model, return the generated code as a string
        ...

    def ask_to_analyze(self, prompt: str) -> str:
        # call your model, return a JSON string describing the style
        ...

backend = MyBackend()
analyzer = StyleAnalyzer(backend)
profile = analyzer.analyze_codebase(Path("."))
code = generate_code("write a logging helper", backend, profile)
```

---

## Deep Analysis

For a richer style profile, `scripts/deep_analyze.py` runs six focused queries (naming, error handling, string formatting, module structure, docstrings, and representative snippets) and synthesizes them into a single detailed profile.

```bash
# Run from the project root; writes style_profile.json
python scripts/deep_analyze.py
```

This is slower than the standard `analyze` command but produces a more detailed profile, which leads to better code generation.

---

## Running Tests

```bash
python tests/test_library.py
```

The test suite uses a `MockBackend` so no live AI backend is required. It exercises the full analyze → generate pipeline.

---

## Project Structure

```
my_code/
├── analyzer.py          # StyleAnalyzer — scans files, builds style profile
├── generator.py         # generate_code() — formats prompt and calls backend
├── ricky_client.py      # Low-level MCP client for the local Ricky/llama server
├── cli.py               # CLI entry point (my-code command)
├── backends/
│   ├── base.py          # AIBackend abstract base class
│   ├── ricky_backend.py # Local LLM via Ricky MCP server
│   ├── claude_backend.py
│   ├── openai_backend.py
│   └── mcp_backend.py   # Placeholder for custom MCP backends
└── utils/
    └── prompts.py       # Prompt templates for extraction, summary, generation
scripts/
└── deep_analyze.py      # Multi-query deep style analysis
tests/
└── test_library.py      # Smoke tests (no live backend required)
```
