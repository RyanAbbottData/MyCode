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

**From PyPI (recommended):**

```bash
pip install mycode-aiagent

# With Claude backend support
pip install "mycode-aiagent[claude]"

# With OpenAI backend support
pip install "mycode-aiagent[openai]"

# With all backends
pip install "mycode-aiagent[all]"
```

**From source:**

```bash
git clone https://github.com/RyanAbbottData/MyCode
cd MyCode
pip install -e .
```

The `my-code` CLI command is registered automatically on install.

---

## Backends

MyCode delegates inference to a pluggable backend. Choose one based on what you have available.

| Backend | Flag | Requirement |
|---|---|---|
| Local LLM | `--backend llama` (default) | MCP server running at `localhost:8000` |
| Anthropic Claude | `--backend claude` | `ANTHROPIC_API_KEY` env var or `--api-key` |
| OpenAI | `--backend openai` | `OPENAI_API_KEY` env var or `--api-key` |
| MyCode server | `--backend mcp` | A running MyCode MCP server at `--mcp-url` |

When `--backend mcp` is used with `analyze` or `generate`, the CLI delegates the entire operation to the running MyCode server — it calls the server's `analyze_codebase` or `generate_code` tool directly instead of running the pipeline locally. This is the recommended way to use MyCode in a multi-project or agentic setup.

### Setting up a local LLM

The `llama` backend expects an MCP server at `http://localhost:8000/mcp` that exposes two tools: one for code generation and one for analysis. Any MCP-compatible wrapper around a local model will work. Here is a recommended setup using [llama.cpp](https://github.com/ggerganov/llama.cpp):

**1. Download a model**

A code-focused model works best. Good options:
- [CodeLlama-7B-Instruct](https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF) — fast, runs on most hardware
- [CodeLlama-13B-Instruct](https://huggingface.co/TheBloke/CodeLlama-13B-Instruct-GGUF) — better quality, needs ~10 GB VRAM
- [DeepSeek-Coder-6.7B-Instruct](https://huggingface.co/TheBloke/deepseek-coder-6.7B-instruct-GGUF) — strong alternative

Download a `.gguf` quantized file (Q4_K_M is a good balance of size and quality).

**2. Start the llama.cpp server**

```bash
# Install llama.cpp (or use a pre-built binary)
pip install llama-cpp-python[server]

# Start the OpenAI-compatible server
python -m llama_cpp.server \
  --model ./models/codellama-7b-instruct.Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8000 \
  --n_ctx 4096
```

**3. Wrap it with an MCP server**

The `llama` backend communicates over MCP, not directly with the llama.cpp HTTP API. You need a thin MCP wrapper that exposes two tools:
- A **code generation tool** (name must not contain `"analyze"`)
- An **analysis tool** (name must contain `"analyze"`)

Both tools accept a `query` string and return the model's completion. A minimal FastMCP wrapper example:

```python
# llm_mcp_server.py
from fastmcp import FastMCP
import requests

mcp = FastMCP("local-llm")
LLM_URL = "http://localhost:8000/v1/completions"

def _complete(prompt: str) -> str:
    resp = requests.post(LLM_URL, json={
        "prompt": prompt,
        "max_tokens": 1024,
        "temperature": 0.1,
    })
    return resp.json()["choices"][0]["text"]

@mcp.tool()
def generate_code(query: str) -> str:
    return _complete(query)

@mcp.tool()
def analyze_code(query: str) -> str:
    return _complete(query)

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

```bash
pip install fastmcp
python llm_mcp_server.py
```

**4. Point MyCode at it**

```bash
my-code --backend llama --ricky-url http://localhost:8000/mcp analyze .
```

Or set a custom URL if your server runs on a different port:

```bash
my-code --backend llama --ricky-url http://localhost:9000/mcp analyze .
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

Delegating to a running MyCode server:
```bash
my-code --backend mcp --mcp-url http://localhost:8000/mcp analyze ./path/to/codebase
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

# Delegate to a running MyCode server
my-code --backend mcp --mcp-url http://localhost:8000/mcp generate "write a rate limiter"
```

---

## CLI Reference

```
my-code [OPTIONS] COMMAND

Options:
  --backend {llama,claude,openai,mcp}   AI backend to use (default: llama)
  --api-key TEXT                         API key for claude/openai backends
  --model TEXT                           Override the default model
  --ricky-url TEXT                       Local LLM MCP server URL (default: http://localhost:8000/mcp)
  --mcp-url TEXT                         Custom MCP server URL (default: http://localhost:8001/mcp)
  --profile TEXT                         Path to style profile JSON (default: style_profile.json)

Commands:
  analyze PATH    Analyze a codebase and write a style profile
    --verbose     Print each file as it is analyzed

  generate TASK   Generate code matching the saved style profile

  serve              Start an MCP server (blocks until Ctrl-C)
    --host TEXT      Host to bind (default: 127.0.0.1)
    --port INT       Port to listen on (default: 8080)
    --daemon         Run as a detached background process
    --pid-file TEXT  PID file path for daemon mode (default: mycode.pid)

  stop               Stop a running daemon server
    --pid-file TEXT  PID file written by 'serve --daemon' (default: mycode.pid)
```

---

## Python API

MyCode is a first-class library. All CLI functionality is available programmatically.

```python
from my_code import StyleAnalyzer, generate_code, make_backend
from pathlib import Path

# Create a backend
backend = make_backend()                           # local LLM (default)
backend = make_backend("claude")                   # Claude (reads ANTHROPIC_API_KEY)
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

## Running as an MCP Server

MyCode can expose itself as an MCP server so any MCP-compatible agent or orchestrator can call its tools directly — no MCP knowledge required.

### Quick start

```bash
# Local LLM backend (default) — foreground, blocks until Ctrl-C
my-code serve

# Claude backend
my-code --backend claude serve --port 8080

# OpenAI backend
my-code --backend openai serve --port 8080

# Bind on all interfaces
my-code --backend claude serve --host 0.0.0.0 --port 8080
```

On startup the server prints the URL and the config snippet to paste:

```
MyCode MCP server running at http://127.0.0.1:8080/mcp
Add to your MCP config:  {"mycode": {"url": "http://127.0.0.1:8080/mcp"}}
```

### Running as a daemon

Add `--daemon` to run the server as a detached background process. The terminal returns immediately and the server keeps running.

```bash
my-code --backend claude serve --daemon
# → MyCode MCP server started as daemon (PID 12345) at http://127.0.0.1:8080/mcp
# → Stop with: my-code stop
```

The PID is written to `mycode.pid` by default. Stop the server with:

```bash
my-code stop
```

When running multiple instances on different ports, use `--pid-file` to keep them separate:

```bash
my-code --backend claude serve --port 8080 --daemon --pid-file mycode-8080.pid
my-code --backend openai serve --port 8081 --daemon --pid-file mycode-8081.pid

my-code stop --pid-file mycode-8080.pid
my-code stop --pid-file mycode-8081.pid
```

### Using the server from the CLI

Start a MyCode server as a daemon, then point `analyze` and `generate` at it with `--backend mcp`. The CLI calls the server's tools directly — the server handles all analysis and generation using whichever LLM it was started with.

```bash
# Start the server (uses a local LLM at port 8001 as its brain)
my-code --backend mcp --mcp-url http://localhost:8001/mcp serve --daemon --port 8000

# Analyze a codebase via the server
my-code --backend mcp --mcp-url http://localhost:8000/mcp analyze ./my_project

# Generate code via the server (loads style_profile.json locally and sends it)
my-code --backend mcp --mcp-url http://localhost:8000/mcp generate "write a retry decorator"

# Stop the server
my-code stop
```

### Connecting from an MCP consumer

Add the printed snippet to your consumer's MCP config file (e.g. `.mcp.json`):

```json
{
  "mycode": { "url": "http://127.0.0.1:8080/mcp" }
}
```

### Tools exposed

| Tool | Required args | Optional args |
|------|--------------|---------------|
| `analyze_codebase` | `path` — directory to analyze | `save_to` — path to save the profile JSON |
| `generate_code` | `task` — what to write | `profile` — inline profile object; `profile_path` — path to a saved profile (default: `style_profile.json`) |

Both tools return plain text. `analyze_codebase` returns the style profile as a JSON string. `generate_code` returns the generated source code.

### Programmatic usage

```python
from my_code import run_server, make_backend

# Blocking — call from a background thread if needed
run_server(backend=make_backend("claude"), host="127.0.0.1", port=8080)
```

Or use `MCPServer` directly for more control:

```python
from my_code import MCPServer, make_backend
import threading

server = MCPServer(make_backend("claude"), host="127.0.0.1", port=8080)
httpd = server.start()                          # binds immediately
port = httpd.server_address[1]                  # actual port (useful when port=0)
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
# ... httpd.shutdown() to stop
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
# Library smoke tests (analyze → generate pipeline)
python tests/test_library.py

# MCP server protocol tests
python -m pytest tests/test_server.py -v
# or
python -m unittest tests/test_server.py
```

Both test suites use a `MockBackend` — no live AI backend required.

---

## Project Structure

```
my_code/
├── analyzer.py          # StyleAnalyzer — scans files, builds style profile
├── generator.py         # generate_code() — formats prompt and calls backend
├── mcp_client.py        # MCPClient (raw LLM wrapper) + MyCodeClient (server delegation)
├── server.py            # MCPServer — exposes analyze/generate as MCP tools
├── cli.py               # CLI entry point (my-code command)
├── backends/
│   ├── base.py          # AIBackend abstract base class
│   ├── ricky_backend.py # Local LLM backend (connects via MCP)
│   ├── claude_backend.py
│   ├── openai_backend.py
│   └── mcp_backend.py   # Generic MCP server backend
└── utils/
    └── prompts.py       # Prompt templates for extraction, summary, generation
scripts/
└── deep_analyze.py      # Multi-query deep style analysis
tests/
├── test_library.py      # Smoke tests for analyze/generate (no live backend)
└── test_server.py       # MCP server protocol tests (no live backend)
```
