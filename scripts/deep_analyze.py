"""
Deep style analysis: runs focused per-dimension LLM queries then synthesizes
a detailed style_profile.json. Run from the project root.
"""
import json
import re
from pathlib import Path

from my_code.backends import make_backend


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def main():
    backend = make_backend()

    def ask(label: str, prompt: str) -> str:
        print(f"  Querying: {label} ...", flush=True)
        return backend.ask_to_analyze(prompt)

    results = {}

    results["naming_types"] = ask("naming + type annotations", """\
Analyze this Python code and return ONLY a JSON object with these exact keys:
{
  "naming_functions": "snake_case or camelCase or PascalCase",
  "naming_classes": "snake_case or camelCase or PascalCase",
  "naming_private": "underscore prefix or other",
  "naming_constants": "UPPER_SNAKE_CASE or other",
  "type_annotations": "full or partial or none",
  "union_syntax": "X|Y or Optional[X] or none",
  "return_annotations": "always or sometimes or never"
}
Return ONLY valid JSON, no explanation.

Code:
def _collect_python_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob("*.py"):
        if not any(part in _SKIP_DIRS for part in path.parts):
            files.append(path)
    return sorted(files)

class MCPClientExample:
    def __init__(self, url: str = "http://localhost:8000/mcp"):
        self.url = url
        self._session_id: str | None = None
        self._tool_name: str | None = None

    def _post(self, method: str, params: dict, timeout: int = 120) -> dict:
        ...

    def ask_for_code(self, prompt: str) -> str:
        ...
""")

    results["error_handling"] = ask("error handling", """\
Analyze this Python code and return ONLY a JSON object with these exact keys:
{
  "exit_style": "sys.exit or raise or both",
  "exception_types": ["list", "of", "exception", "classes", "used"],
  "guard_style": "early return or nested if",
  "error_messages": "f-string or format or concat"
}
Return ONLY valid JSON, no explanation.

Code:
def cmd_analyze(args):
    root = Path(args.codebase).resolve()
    if not root.exists():
        sys.exit(f"Error: directory not found: {root}")

def cmd_generate(args):
    profile_path = Path(args.profile)
    if not profile_path.exists():
        sys.exit(
            f"Error: style profile not found at {profile_path}. "
            "Run 'analyze' first."
        )

def _discover_tools(self):
    tools = self._post("tools/list", {}).get("tools", [])
    if not tools:
        raise RuntimeError("MCP server exposes no tools")
    if not self._tool_name:
        raise RuntimeError("MCP server exposes no coding tool")

def analyze_codebase(self, root: Path, verbose: bool = False) -> dict:
    files = _collect_python_files(root)
    if not files:
        raise FileNotFoundError(f"No Python files found under {root}")
    if not observations:
        raise RuntimeError("No style data could be extracted from any file.")
""")

    results["strings_and_flow"] = ask("strings and control flow", """\
Analyze this Python code and return ONLY a JSON object with these exact keys:
{
  "string_formatting": "f-string or format or percent or concat",
  "comprehensions": "used or avoided",
  "ternary": "used or avoided",
  "chaining": "method chaining style: heavy or light"
}
Return ONLY valid JSON, no explanation.

Code:
print(f"Connecting to MCP server at {args.mcp_url} ...")
print(f"Connected to MCP server — tools: '{self._tool_name}', '{self._tool_name_analyze}'")
raise ValueError(f"No data event in SSE body:\\n{text[:400]}")
raise RuntimeError(f"MCP error ({method}): {msg['error']}")
print(f"  [warn] Could not parse style from {path.name}: {e}")

files = [p for p in root.rglob("*.py")
         if not any(part in _SKIP_DIRS for part in p.parts)]

tools = self._post("tools/list", {}).get("tools", [])
inner_str = outer.get("result", text)
""")

    results["module_structure"] = ask("module structure", """\
Analyze this Python module layout and return ONLY a JSON object with these exact keys:
{
  "module_docstring": "present or absent",
  "import_grouping": "stdlib then third-party then local, or flat",
  "constants_placement": "after imports or inline or both",
  "main_guard": "present or absent",
  "function_before_class": true or false
}
Return ONLY valid JSON, no explanation.

Layout of my_code.py:
1. Module docstring (usage examples)
2. import argparse, sys, pathlib  (stdlib)
3. from analyzer import StyleAnalyzer  (local)
4. from mcp_client import MCPClient  (local)
5. from utils.prompts import CODE_GENERATION_PROMPT  (local)
6. DEFAULT_PROFILE = Path("style_profile.json")  (constant)
7. def cmd_analyze(args): ...
8. def cmd_generate(args): ...
9. def main(): ...
10. if __name__ == "__main__": main()
""")

    results["docs"] = ask("docstrings and comments", """\
Analyze these docstrings and comments and return ONLY a JSON object with these exact keys:
{
  "docstring_style": "Google or NumPy or plain or none",
  "docstring_coverage": "all public or selected or none",
  "inline_comment_density": "sparse or moderate or heavy",
  "inline_comment_style": "explain why or explain what or mixed"
}
Return ONLY valid JSON, no explanation.

Examples:
def _parse_sse_result(text: str) -> dict:
    \"\"\"Extract the first JSON-RPC result/error from an SSE response body.\"\"\"

class MCPClientExample:
    \"\"\"MCP client for local LLM server using the Streamable HTTP transport.

    Flow:
      1. POST /mcp  initialize -> SSE body + Mcp-Session-Id header
      2. POST /mcp  <any call> -> SSE body  (Mcp-Session-Id in every request)
    \"\"\"

# Give the LLM explicit, complete prompts.
_PROTOCOL = "2024-11-05"

# keep prompts within CodeLlama 7B's context
_MAX_FILE_CHARS = 1500
""")

    results["snippets"] = ask("representative snippets", """\
Look at this Python code and return ONLY a JSON object with this exact key:
{
  "snippets": ["snippet1", "snippet2", "snippet3"]
}
Choose 3 short verbatim excerpts (each under 5 lines) that best demonstrate the coding style.
Return ONLY valid JSON, no explanation.

Code:
def _parse_sse_result(text: str) -> dict:
    \"\"\"Extract the first JSON-RPC result/error from an SSE response body.\"\"\"
    for line in text.splitlines():
        if line.startswith("data:"):
            payload = line[5:].strip()
            if payload and payload != "[DONE]":
                return json.loads(payload)
    raise ValueError(f"No data event in SSE body:\\n{text[:400]}")

def _collect_python_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob("*.py"):
        if not any(part in _SKIP_DIRS for part in path.parts):
            files.append(path)
    return sorted(files)

def _extract_json(text: str) -> dict:
    match = re.search(r"\\{.*\\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in response:\\n{text[:300]}")
    return json.loads(match.group())
""")

    print("\nRaw results:")
    for k, v in results.items():
        print(f"\n[{k}]\n{v[:300]}")

    parsed = {k: _extract_json(v) for k, v in results.items()}

    n = parsed.get("naming_types", {})
    e = parsed.get("error_handling", {})
    s = parsed.get("strings_and_flow", {})
    m = parsed.get("module_structure", {})
    d = parsed.get("docs", {})
    snip = parsed.get("snippets", {})

    profile = {
        "naming": {
            "functions": n.get("naming_functions", "snake_case"),
            "classes": n.get("naming_classes", "PascalCase"),
            "variables": "snake_case",
            "constants": n.get("naming_constants", "UPPER_SNAKE_CASE"),
            "private_prefix": n.get("naming_private", "underscore prefix"),
            "notes": "verb_noun for functions (cmd_analyze, ask_for_code), leading underscore for private (_post, _discover_tools)",
        },
        "type_annotations": {
            "usage": n.get("type_annotations", "full"),
            "union_syntax": n.get("union_syntax", "X|Y"),
            "return_annotations": n.get("return_annotations", "always"),
            "notes": "Modern PEP 604 union syntax (str | None), built-in generics (list[Path], dict)",
        },
        "structure": {
            "import_grouping": m.get("import_grouping", "stdlib then third-party then local"),
            "constants_placement": m.get("constants_placement", "after imports"),
            "function_before_class": m.get("function_before_class", True),
            "class_method_order": "init_first, private helpers before public interface",
            "main_guard": m.get("main_guard", "present"),
            "module_docstring": m.get("module_docstring", "present on entry-point modules"),
            "preferred_length": "short",
        },
        "error_handling": {
            "exit_style": e.get("exit_style", "sys.exit for CLI entry points, raise for library code"),
            "exception_types": e.get("exception_types", ["RuntimeError", "ValueError", "FileNotFoundError"]),
            "guard_style": e.get("guard_style", "early return"),
            "error_messages": e.get("error_messages", "f-string"),
        },
        "strings_and_flow": {
            "string_formatting": s.get("string_formatting", "f-string"),
            "comprehensions": s.get("comprehensions", "used"),
            "method_chaining": s.get("chaining", "light"),
            "ternary": s.get("ternary", "avoided"),
        },
        "comments": {
            "docstring_style": d.get("docstring_style", "plain"),
            "docstring_coverage": d.get("docstring_coverage", "selected"),
            "inline_density": d.get("inline_comment_density", "sparse"),
            "inline_style": d.get("inline_comment_style", "explain why"),
        },
        "representative_snippets": snip.get("snippets", [
            "def _parse_sse_result(text: str) -> dict:\n    \"\"\"Extract the first JSON-RPC result/error from an SSE response body.\"\"\"\n    for line in text.splitlines():\n        if line.startswith(\"data:\"):\n            payload = line[5:].strip()\n            if payload and payload != \"[DONE]\":\n                return json.loads(payload)\n    raise ValueError(f\"No data event in SSE body:\\n{text[:400]}\")",
            "def _collect_python_files(root: Path) -> list[Path]:\n    files = []\n    for path in root.rglob(\"*.py\"):\n        if not any(part in _SKIP_DIRS for part in path.parts):\n            files.append(path)\n    return sorted(files)",
            "def _extract_json(text: str) -> dict:\n    match = re.search(r\"\\{.*\\}\", text, re.DOTALL)\n    if not match:\n        raise ValueError(f\"No JSON found in response:\\n{text[:300]}\")\n    return json.loads(match.group())",
        ]),
    }

    out = Path("style_profile.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

    print(f"\nDetailed profile saved to {out}")
    print(json.dumps(profile, indent=2))


if __name__ == "__main__":
    main()
