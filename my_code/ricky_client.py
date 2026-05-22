import json
import uuid

import requests

# Ricky's own instructions: give it explicit, complete prompts.
_PROTOCOL = "2024-11-05"


def _parse_sse_result(text: str) -> dict:
    """Extract the first JSON-RPC result/error from an SSE response body."""
    for line in text.splitlines():
        if line.startswith("data:"):
            payload = line[5:].strip()
            if payload and payload != "[DONE]":
                return json.loads(payload)
    raise ValueError(f"No data event in SSE body:\n{text[:400]}")


class RickyClient:
    """MCP client for ricky using the Streamable HTTP transport.

    Flow:
      1. POST /mcp  initialize  → SSE body + Mcp-Session-Id header
      2. POST /mcp  <any call>  → SSE body  (Mcp-Session-Id in every request)
    """

    def __init__(self, url: str = "http://localhost:8000/mcp"):
        self.url = url
        self._session_id: str | None = None
        self._tool_name: str | None = None
        self._tool_name_analyze: str | None = None
        self._initialize()
        self._discover_tools()
        print(f"Connected to ricky — tools: '{self._tool_name}', '{self._tool_name_analyze}'")

    def _post(self, method: str, params: dict, timeout: int = 120) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params,
        }
        resp = requests.post(self.url, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()

        if "Mcp-Session-Id" in resp.headers:
            self._session_id = resp.headers["Mcp-Session-Id"]

        msg = _parse_sse_result(resp.text)
        if "error" in msg:
            raise RuntimeError(f"MCP error ({method}): {msg['error']}")
        return msg.get("result", {})

    def _initialize(self):
        self._post("initialize", {
            "protocolVersion": _PROTOCOL,
            "capabilities": {},
            "clientInfo": {"name": "style-agent", "version": "1.0"},
        })

    def _discover_tools(self):
        tools = self._post("tools/list", {}).get("tools", [])
        if not tools:
            raise RuntimeError("Ricky exposes no tools")
        for t in tools:
            name = t["name"]
            if "analyze" in name and self._tool_name_analyze is None:
                self._tool_name_analyze = name
            elif self._tool_name is None:
                self._tool_name = name
        if not self._tool_name:
            raise RuntimeError("Ricky exposes no coding tool")
        if not self._tool_name_analyze:
            raise RuntimeError("Ricky exposes no analyze tool")

    def _parse_content(self, result: dict) -> str:
        content = result.get("content", [])
        if isinstance(content, list):
            for block in content:
                if block.get("type") == "text":
                    text = block.get("text", "")
                    # Ricky wraps llama.cpp output: {"result": "<completion JSON>"}
                    try:
                        outer = json.loads(text)
                        inner_str = outer.get("result", text)
                        inner = json.loads(inner_str)
                        return inner["choices"][0]["text"]
                    except (json.JSONDecodeError, KeyError, TypeError):
                        return text
        return str(content)

    def ask_for_code(self, prompt: str) -> str:
        result = self._post("tools/call", {
            "name": self._tool_name,
            "arguments": {"query": prompt},
        })
        return self._parse_content(result)

    def ask_to_analyze(self, prompt: str) -> str:
        result = self._post("tools/call", {
            "name": self._tool_name_analyze,
            "arguments": {"query": prompt},
        }, timeout=600)
        return self._parse_content(result)
