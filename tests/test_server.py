"""
Tests for the MyCode MCP server.
Spins up a real ThreadingHTTPServer against a MockBackend and exercises the protocol.
No live AI backend required.
"""
import io
import json
import socket
import threading
import unittest
from pathlib import Path

import requests

from my_code.server import ANALYZE_TOOL, MCPServer
from my_code import AIBackend

# ── Mock backend (same contract as the one in test_library.py) ────────────────

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


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _post(url: str, method: str, params: dict, session_id: str | None = None) -> requests.Response:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    return requests.post(
        url,
        json={"jsonrpc": "2.0", "id": "1", "method": method, "params": params},
        headers=headers,
        timeout=10,
    )


def _parse(resp: requests.Response) -> dict:
    for line in resp.text.splitlines():
        if line.startswith("data:"):
            return json.loads(line[5:].strip())
    raise AssertionError(f"No SSE data line in response: {resp.text[:300]}")


class TestMCPServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        port = _free_port()
        cls.url = f"http://127.0.0.1:{port}/mcp"
        server = MCPServer(MockBackend(), host="127.0.0.1", port=port)
        cls.httpd = server.start()
        t = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        t.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def test_initialize(self):
        resp = _post(self.url, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"},
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Mcp-Session-Id", resp.headers)
        msg = _parse(resp)
        self.assertIn("result", msg)
        self.assertEqual(msg["result"]["serverInfo"]["name"], "mycode")

    def test_tools_list(self):
        resp = _post(self.url, "tools/list", {})
        self.assertEqual(resp.status_code, 200)
        msg = _parse(resp)
        tools = {t["name"] for t in msg["result"]["tools"]}
        self.assertEqual(tools, {"analyze_codebase", "generate_code"})

    def test_analyze_codebase(self):
        path = str(Path(__file__).parent.parent / "my_code")
        resp = _post(self.url, "tools/call", {
            "name": "analyze_codebase",
            "arguments": {"path": path},
        })
        self.assertEqual(resp.status_code, 200)
        msg = _parse(resp)
        text = msg["result"]["content"][0]["text"]
        profile = json.loads(text)
        self.assertIn("naming", profile)

    def test_generate_code(self):
        resp = _post(self.url, "tools/call", {
            "name": "generate_code",
            "arguments": {"task": "write a greeting function", "profile": MOCK_PROFILE},
        })
        self.assertEqual(resp.status_code, 200)
        msg = _parse(resp)
        code = msg["result"]["content"][0]["text"]
        self.assertTrue(len(code) > 0)
        self.assertIn("def", code)

    def test_unknown_method(self):
        resp = _post(self.url, "nonexistent/method", {})
        self.assertEqual(resp.status_code, 200)
        msg = _parse(resp)
        self.assertIn("error", msg)
        self.assertEqual(msg["error"]["code"], -32601)

    def test_unknown_tool(self):
        resp = _post(self.url, "tools/call", {
            "name": "does_not_exist",
            "arguments": {},
        })
        self.assertEqual(resp.status_code, 200)
        msg = _parse(resp)
        self.assertIn("error", msg)
        self.assertEqual(msg["error"]["code"], -32602)


class TestMCPServerStdio(unittest.TestCase):
    """The stdio transport used by the Claude Code plugin."""

    def _run(self, *messages, tools=None) -> list[dict]:
        """Feed JSON-RPC messages through serve_stdio and return the parsed responses."""
        stdin = io.StringIO("".join(json.dumps(m) + "\n" for m in messages))
        stdout = io.StringIO()
        server = MCPServer(MockBackend(), tools=tools)
        server.serve_stdio(stdin=stdin, stdout=stdout)
        return [json.loads(line) for line in stdout.getvalue().splitlines() if line]

    def test_initialize_and_tools_list(self):
        msgs = self._run(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["result"]["serverInfo"]["name"], "mycode")
        tools = {t["name"] for t in msgs[1]["result"]["tools"]}
        self.assertEqual(tools, {"analyze_codebase", "generate_code"})

    def test_tool_filtering(self):
        """The plugin narrows the surface to analysis only."""
        msgs = self._run(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            tools=[ANALYZE_TOOL],
        )
        tools = {t["name"] for t in msgs[0]["result"]["tools"]}
        self.assertEqual(tools, {"analyze_codebase"})

    def test_notification_gets_no_response(self):
        """Messages without an id must produce no output line — including unknown methods."""
        msgs = self._run(
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        )
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["id"], 1)

    def test_library_prints_do_not_corrupt_stdout(self):
        """analyze_codebase prints progress; stdout is the protocol channel, so it must stay clean."""
        path = str(Path(__file__).parent.parent / "my_code")
        msgs = self._run({
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "analyze_codebase", "arguments": {"path": path}},
        })
        self.assertEqual(len(msgs), 1)
        profile = json.loads(msgs[0]["result"]["content"][0]["text"])
        self.assertIn("naming", profile)

    def test_malformed_line(self):
        msgs = self._run_raw("not json\n")
        self.assertEqual(msgs[0]["error"]["code"], -32700)

    def _run_raw(self, text: str) -> list[dict]:
        stdout = io.StringIO()
        MCPServer(MockBackend()).serve_stdio(stdin=io.StringIO(text), stdout=stdout)
        return [json.loads(line) for line in stdout.getvalue().splitlines() if line]


if __name__ == "__main__":
    unittest.main()
