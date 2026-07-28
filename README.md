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

## Use as a Claude Code plugin

MyCode ships as a [Claude Code](https://claude.com/claude-code) plugin as well as a library. The plugin
lets Claude analyze your codebase's style and then write new code in that style itself.

*Looking for the library or the `my-code` CLI? Those are documented below, starting at
[Installation](#installation).*

### Install

The plugin runs the installed Python package, so install that first:

```bash
pip install mycode-aiagent[claude]
```

Then add this repo as a plugin marketplace and install:

```bash
claude plugin marketplace add RyanAbbottData/MyCode
claude plugin install mycode@mycode
```

To develop against a local checkout instead, skip the marketplace and run:

```bash
pip install -e .
claude --plugin-dir /path/to/MyCode
```

### What you get

| Component | Name | Purpose |
|-----------|------|---------|
| MCP tool | `analyze_codebase` | Analyze a directory and return its style profile |
| Skill | `/mycode:mycode-style` | Loads `style_profile.json` so Claude writes in your style |

The plugin deliberately exposes **analysis only** — not `generate_code`. Inside Claude Code, calling
`generate_code` would mean Claude asking a second LLM to write the code and pasting the result back.
Claude is already the code generator, so the skill hands it the profile and lets it write directly.
The HTTP server (`my-code serve`) still exposes both tools for non-Claude consumers.

### Configuration

The plugin's MCP server reads its backend configuration from the environment:

| Variable | Default | Purpose |
|----------|---------|---------|
| `MYCODE_BACKEND` | `claude` | Backend for analysis: `claude`, `openai`, or `local` |
| `MYCODE_MODEL` | backend default | Override the model |
| `MYCODE_LLM_URL` | `http://localhost:8080/v1` | Local LLM server URL when `MYCODE_BACKEND=local` |

API keys come from `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` as usual. Note that Claude Code subscription
auth does **not** set `ANTHROPIC_API_KEY` — set it yourself, or point the plugin at a local model:

```bash
export MYCODE_BACKEND=local
```

The server starts regardless of whether a key is present; a missing key surfaces as an error on the
tool call, not as a failed plugin load.

### Using it

#### 1. Confirm the plugin loaded

Run `/plugin` inside Claude Code, or just ask:

> list your MCP servers

You should see `mycode (plugin)`. If it is missing, see [Troubleshooting](#troubleshooting) below.

#### 2. Build the style profile (once per project)

Ask Claude to analyze the project:

> Analyze this repo's coding style and save it to style_profile.json

Claude calls `analyze_codebase` with `path` and `save_to`, and writes the profile to disk. This is the
slow step — see the cost note at the end of this section.

You can also build the profile outside Claude Code with the CLI; the plugin reads whatever is on disk:

```bash
my-code analyze . --verbose
```

#### 3. Write code in your style

Just ask for code normally:

> Add a function that loads config from a YAML file

The `mycode-style` skill fires on its own when a `style_profile.json` is present, reads it, and applies
your conventions — naming, import grouping, docstring style, error handling — before Claude writes
anything. To force it explicitly:

```
/mycode:mycode-style
```

#### What the skill actually applies

| Profile key | Effect on generated code |
|-------------|--------------------------|
| `naming` | Identifier conventions for functions, classes, variables, constants |
| `structure` | Import grouping, module layout, class/method ordering, function length |
| `comments` | Docstring style and inline comment density |
| `representative_snippets` | Formatting ground truth — copied when the prose fields are ambiguous |

The profile schema varies by backend, so the skill reads whichever keys are present rather than assuming a
fixed shape. It describes **style, not correctness**: it never overrides your `CLAUDE.md`, your linter
config, or an explicit instruction in your prompt.

### Troubleshooting

| Symptom | Cause and fix |
|---------|---------------|
| `mycode` missing from the MCP server list | `python` or the package isn't resolvable. Check with `python -m my_code mcp-stdio` — it should sit waiting on stdin, not error. If it fails, `pip install mycode-aiagent` into the same interpreter that `python` resolves to. |
| Tool call returns *"Claude backend requires ANTHROPIC_API_KEY"* | Expected when using subscription auth. Set the key, or `export MYCODE_BACKEND=local` and start a local model. The server itself still loads fine. |
| Skill never fires | No `style_profile.json` in the working directory. Run step 2, or invoke `/mycode:mycode-style` explicitly. |
| Generated code ignores the profile | An explicit instruction in your prompt, or your `CLAUDE.md`, takes precedence by design. |

To smoke-test the MCP server without Claude Code at all:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python -m my_code mcp-stdio
```

It should print one JSON line advertising `analyze_codebase`.

> **Cost note.** Analysis makes `2N-1` sequential LLM calls for `N` Python files, so large repos take a
> while and are not free. Run it once and commit the resulting `style_profile.json` so your whole team
> shares one profile.

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
| Anthropic Claude | `--backend claude` (default) | `ANTHROPIC_API_KEY` env var or `--api-key` |
| OpenAI | `--backend openai` | `OPENAI_API_KEY` env var or `--api-key` |
| Local LLM (OpenAI-compatible) | `--backend local` | LLM server at `--llm-url` (default: `http://localhost:8080/v1`) |
| Any MCP server | `--backend mcp` | A running MyCode MCP server at `--mcp-url` |

When `--backend mcp` is used with `analyze` or `generate`, the CLI delegates the entire operation to the running MyCode server — it calls the server's `analyze_codebase` or `generate_code` tool directly instead of running the pipeline locally. This is the recommended way to use MyCode in a multi-project or agentic setup.

### Setting up a local LLM

Use `--backend local` to connect MyCode directly to any OpenAI-compatible LLM server (llama.cpp, LM Studio, Ollama, etc.) — no wrapper needed. Point `--llm-url` at the server's `/v1` base URL:

```bash
# Start your local LLM server (example: llama.cpp)
llama-server -m ./models/codellama-7b-instruct.Q4_K_M.gguf --port 8080 --chat-template llama2 --ctx-size 4096

# Analyze using the local LLM directly
my-code --backend local --llm-url http://localhost:8080/v1 analyze ./my_project

# Or start a MyCode MCP server backed by your local LLM
my-code --backend local --llm-url http://localhost:8080/v1 serve --port 8000 --daemon
```

> **Timeout note**: CPU-based local LLMs can be slow (a quantized 7B model generates ~3 tokens/sec on CPU). The default `--timeout 600` (10 minutes per LLM call) is designed to accommodate this. If you see `Request timed out.` errors, increase it: `--timeout 1800`. When delegating analysis via `--backend mcp`, also pass a generous `--timeout` on the client side to match the server's total analysis time across all files.
>
> The `local` backend sends `max_tokens=2048` per call, overriding the llama-server default of 128 tokens, so style analysis JSON is never silently truncated.

**JSON output reliability:** The `local` backend requests `response_format: json_object` (constrained decoding) for all analysis calls. When supported by the server, this forces the model to produce valid JSON at the sampling level — eliminating hallucinated non-JSON output regardless of model size. If the server rejects it (HTTP 400/422 — common on older llama.cpp or Ollama builds), the backend automatically retries with a simplified 4-field flat prompt that small models can follow reliably without grammar constraints. Other errors (timeouts, connection failures) propagate normally so they are not silently swallowed.

| Server | Constrained JSON (`response_format`) |
|---|---|
| llama.cpp (`llama-server`) | ✓ |
| Ollama | ✓ |
| LM Studio | ✓ |
| vLLM | ✓ |
| text-generation-webui | varies by version |

**Chat template / instruction format:** If your local server does not automatically apply the model's chat template, the model may ignore instructions and return conversational text instead of JSON. Two ways to fix this:

1. **Server-side (recommended):** Pass `--chat-template llama2 --ctx-size 4096` when starting llama.cpp. The chat template ensures instructions are followed; the context size ensures the full prompt fits without truncation.
   ```bat
   llama-server.exe -m codellama-7b-instruct.Q4_K_M.gguf --port 8080 --chat-template llama2 --ctx-size 4096
   ```

2. **Client-side:** Pass `--prompt-format llama2` to `my-code` to have the client wrap prompts in `[INST]`/`[/INST]` before sending.
   ```bash
   my-code --backend local --prompt-format llama2 --llm-url http://localhost:8080/v1 analyze ./my_project
   ```

If you need a full MCP-wrapped setup instead (e.g. the local LLM exposes only `/v1/completions` without chat completions), here is a recommended pattern using [llama.cpp](https://github.com/ggerganov/llama.cpp):

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

The `mcp` backend communicates over MCP, not directly with the llama.cpp HTTP API. You need a thin MCP wrapper that exposes two tools:
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
my-code --backend mcp --mcp-url http://localhost:8000/mcp analyze .
```

Or set a custom URL if your server runs on a different port:

```bash
my-code --backend mcp --mcp-url http://localhost:9000/mcp analyze .
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
my-code --backend local --llm-url http://localhost:8080/v1 analyze ./path/to/codebase
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
  --backend {claude,openai,local,mcp}    AI backend to use (default: claude)
  --api-key TEXT                         API key for claude/openai backends
  --model TEXT                           Override the default model
  --mcp-url TEXT                         MyCode MCP server URL (mcp backend, default: http://localhost:8001/mcp)
  --llm-url TEXT                         Base URL of a local OpenAI-compatible LLM server (local backend, default: http://localhost:8080/v1)
  --timeout INT                          Request timeout in seconds (default: 600; local LLMs may need 600+)
  --prompt-format {openai,llama2}        Prompt wrapping for local backend (default: openai). Use 'llama2' if your server does not apply a chat template automatically.
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

  mcp-stdio          Serve MCP over stdin/stdout (used by the Claude Code plugin)
```

---

## Python API

MyCode is a first-class library. All CLI functionality is available programmatically.

```python
from my_code import StyleAnalyzer, generate_code, make_backend
from pathlib import Path

# Create a backend
backend = make_backend("claude")                                              # Claude (reads ANTHROPIC_API_KEY)
backend = make_backend("openai", api_key="sk-...")                            # OpenAI (GPT models)
backend = make_backend("local", llm_url="http://localhost:8080/v1")                            # Local LLM (OpenAI-compatible)
backend = make_backend("local", llm_url="http://localhost:8080/v1", prompt_format="llama2")  # Local LLM with explicit [INST] wrapping
backend = make_backend("mcp",   mcp_url="http://localhost:8000/mcp")          # Delegate to a MyCode server

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

    def ask_to_analyze(self, prompt: str, fallback_prompt: str | None = None) -> str:
        # call your model, return a JSON string describing the style
        # fallback_prompt is a simpler version used when the backend cannot enforce JSON output
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
# Claude backend — foreground, blocks until Ctrl-C
my-code --backend claude serve --port 8080

# OpenAI backend
my-code --backend openai serve --port 8080

# Local LLM (OpenAI-compatible server on port 8080)
# Use --timeout 600+ for CPU-based models; the server passes this to the openai SDK per call
my-code --backend local --llm-url http://localhost:8080/v1 --timeout 600 serve --port 8000

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
# Start the server backed by a local LLM
my-code --backend local --llm-url http://localhost:8080/v1 serve --daemon --port 8000

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
├── server.py            # MCPServer — exposes analyze/generate as MCP tools (HTTP + stdio)
├── cli.py               # CLI entry point (my-code command)
├── backends/
│   ├── base.py          # AIBackend abstract base class
│   ├── claude_backend.py
│   ├── openai_backend.py  # OpenAIBackend + LocalBackend (with --prompt-format support)
│   └── mcp_backend.py   # Generic MCP server backend
└── utils/
    └── prompts.py       # Prompt templates for extraction, summary, generation
scripts/
└── deep_analyze.py      # Multi-query deep style analysis
tests/
├── test_library.py      # Smoke tests for analyze/generate (no live backend)
└── test_server.py       # MCP server protocol tests, HTTP + stdio (no live backend)
.claude-plugin/
├── plugin.json          # Claude Code plugin manifest (declares the stdio MCP server)
└── marketplace.json     # Lets this repo be added as a plugin marketplace
skills/
└── mycode-style/
    └── SKILL.md         # Skill that loads style_profile.json into Claude's context
```
