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

    def ask_to_analyze(self, prompt: str, fallback_prompt: str | None = None) -> str:
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

try:
    make_backend("mcp", mcp_url="http://localhost:19999/mcp")
    assert False, "Should have raised — no MCP server at port 19999"
except Exception as e:
    assert "Connection" in type(e).__name__ or "refused" in str(e).lower(), (
        f"Expected a connection error, got: {type(e).__name__}: {e}"
    )
    print(f"  mcp: correctly attempts connection ({type(e).__name__})")


# ── Test 6: LocalBackend fallback prompt fires on BadRequestError ─────────────
print("Test 6: LocalBackend uses fallback prompt on BadRequestError ...")
import unittest.mock as mock
import openai as _openai

_fake_msg = mock.Mock()
_fake_msg.content = '{"naming_style": "snake_case"}'
_fake_choice = mock.Mock()
_fake_choice.message = _fake_msg
_fake_response = mock.Mock()
_fake_response.choices = [_fake_choice]

_calls = []

def _fake_create(**kwargs):
    _calls.append(kwargs)
    if "response_format" in kwargs:
        raise _openai.BadRequestError(
            message="response_format not supported",
            response=mock.Mock(status_code=400, headers={}),
            body={"error": {"message": "response_format not supported"}},
        )
    return _fake_response

with mock.patch("openai.OpenAI") as MockOpenAI:
    mock_client = mock.Mock()
    mock_client.chat.completions.create.side_effect = _fake_create
    MockOpenAI.return_value = mock_client
    from my_code.backends.openai_backend import LocalBackend
    lb = LocalBackend(api_key="test", base_url="http://localhost:8080/v1")
    result = lb.ask_to_analyze("full prompt", fallback_prompt="simple prompt")

assert result == '{"naming_style": "snake_case"}', f"Unexpected result: {result}"
assert len(_calls) == 2, f"Expected 2 calls, got {len(_calls)}"
assert "response_format" not in _calls[1], "Second call should not have response_format"
assert _calls[1]["messages"][-1]["content"] == "simple prompt", "Second call should use fallback prompt"
print("  PASS")

# ── Test 7: LocalBackend propagates non-format errors ────────────────────────
print("Test 7: LocalBackend propagates non-format errors ...")

def _raise_timeout(**_):
    raise _openai.APITimeoutError(request=mock.Mock())

with mock.patch("openai.OpenAI") as MockOpenAI:
    mock_client = mock.Mock()
    mock_client.chat.completions.create.side_effect = _raise_timeout
    MockOpenAI.return_value = mock_client
    from my_code.backends.openai_backend import LocalBackend
    lb = LocalBackend(api_key="test", base_url="http://localhost:8080/v1")
    try:
        lb.ask_to_analyze("prompt", fallback_prompt="fallback")
        assert False, "Should have raised APITimeoutError"
    except _openai.APITimeoutError:
        pass
print("  PASS")

print("\nAll tests passed.")
