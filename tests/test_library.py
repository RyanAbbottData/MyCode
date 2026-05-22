"""
Smoke test: exercises the full analyze -> generate flow using a mock backend.
Confirms the library API works correctly for any backend implementation.
"""
import json
from pathlib import Path
from my_code import StyleAnalyzer, generate_code, make_backend, AIBackend

# ── Mock backend ──────────────────────────────────────────────────────────────

MOCK_PROFILE = {
    "naming": {"functions": "snake_case", "classes": "PascalCase"},
    "comments": {"docstring_style": "plain"},
    "representative_snippets": ["def foo(x: int) -> str:\n    return str(x)"],
}

class MockBackend(AIBackend):
    max_file_chars = 6000

    def ask_to_analyze(self, prompt: str) -> str:
        return json.dumps(MOCK_PROFILE)

    def ask_for_code(self, prompt: str) -> str:
        return "def hello(name: str) -> str:\n    return f'Hello, {name}'"

# ── Test 1: StyleAnalyzer.analyze_file ────────────────────────────────────────
print("Test 1: analyze_file ...")
backend = MockBackend()
analyzer = StyleAnalyzer(backend)
result = analyzer.analyze_file(Path("my_code/analyzer.py"))
assert result == MOCK_PROFILE, f"Expected profile, got: {result}"
print("  PASS")

# ── Test 2: StyleAnalyzer.analyze_codebase ────────────────────────────────────
print("Test 2: analyze_codebase ...")
profile = analyzer.analyze_codebase(Path("my_code"))
assert "naming" in profile, f"Profile missing 'naming': {profile}"
print(f"  PASS — profile keys: {list(profile.keys())}")

# ── Test 3: save_profile / load_profile round-trip ────────────────────────────
print("Test 3: save/load profile ...")
tmp = Path("_test_profile.json")
StyleAnalyzer.save_profile(profile, tmp)
loaded = StyleAnalyzer.load_profile(tmp)
assert loaded == profile
tmp.unlink()
print("  PASS")

# ── Test 4: generate_code ─────────────────────────────────────────────────────
print("Test 4: generate_code ...")
code = generate_code(task="write a greeting function", backend=backend, profile=profile)
assert "def hello" in code, f"Unexpected output: {code}"
print(f"  PASS — got:\n    {code}")

# ── Test 5: make_backend error messages ───────────────────────────────────────
print("Test 5: make_backend error messages ...")
import os; os.environ.pop("ANTHROPIC_API_KEY", None); os.environ.pop("OPENAI_API_KEY", None)

try:
    make_backend("claude")
    assert False, "Should have raised"
except ValueError as e:
    assert "ANTHROPIC_API_KEY" in str(e)
    print(f"  claude: {e}")

try:
    make_backend("openai")
    assert False, "Should have raised"
except ValueError as e:
    assert "OPENAI_API_KEY" in str(e)
    print(f"  openai: {e}")

mcp = make_backend("mcp")
try:
    mcp.ask_for_code("test")
except NotImplementedError as e:
    print(f"  mcp placeholder: {e}")

print("\nAll tests passed.")
