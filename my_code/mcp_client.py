import json
import uuid

import requests

_PROTOCOL = "2024-11-05"


def _parse_sse_result(text: str) -> dict:
    for line in text.splitlines():
        if line.startswith("data:"):
            payload = line[5:].strip()
            if payload and payload != "[DONE]":
                return json.loads(payload)
    raise ValueError(f"No data event in SSE body:\n{text[:400]}")


class MCPClient:
    """Generic MCP client using the Streamable HTTP transport.

    Flow:
      1. POST /mcp  initialize  → SSE body + Mcp-Session-Id header
      2. POST /mcp  tools/list  → discover available tools
      3. POST /mcp  tools/call  → invoke a tool
    """

    def __init__(self, url: str = "http://localhost:8001/mcp", timeout: int = 120):
        self.url = url
        self._timeout = timeout
        self._session_id: str | None = None
        self._tool_name: str | None = None
        self._tool_name_analyze: str | None = None
        self._code_arg: str = "query"
        self._analyze_arg: str = "query"
        self._initialize()
        self._discover_tools()
        print(f"Connected to MCP server — tools: '{self._tool_name}', '{self._tool_name_analyze}'")

    def _post(self, method: str, params: dict) -> dict:
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
        resp = requests.post(self.url, json=payload, headers=headers, timeout=self._timeout)
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

    @staticmethod
    def _first_arg(tool: dict) -> str:
        schema = tool.get("inputSchema", {})
        required = schema.get("required", [])
        if required:
            return required[0]
        props = schema.get("properties", {})
        return next(iter(props), "query")

    def _discover_tools(self):
        tools = self._post("tools/list", {}).get("tools", [])
        if not tools:
            raise RuntimeError("MCP server exposes no tools")

        for t in tools:
            name = t["name"]
            arg = self._first_arg(t)
            if "analyze" in name and self._tool_name_analyze is None:
                self._tool_name_analyze = name
                self._analyze_arg = arg
            elif self._tool_name is None:
                self._tool_name = name
                self._code_arg = arg

        if not self._tool_name:
            self._tool_name = tools[0]["name"]
            self._code_arg = self._first_arg(tools[0])
        if not self._tool_name_analyze:
            self._tool_name_analyze = self._tool_name
            self._analyze_arg = self._code_arg

    def _extract_text(self, result: dict) -> str:
        content = result.get("content", [])
        if isinstance(content, list):
            for block in content:
                if block.get("type") == "text":
                    return self._unwrap_llm_response(block.get("text", ""))
        return str(content)

    @staticmethod
    def _unwrap_llm_response(text: str) -> str:
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "choices" in data:
                choices = data["choices"]
                if choices:
                    choice = choices[0]
                    if "text" in choice:
                        return choice["text"]
                    content = choice.get("message", {}).get("content")
                    if content:
                        return content
        except (json.JSONDecodeError, KeyError, IndexError):
            pass
        return text

    def ask_for_code(self, prompt: str) -> str:
        result = self._post("tools/call", {
            "name": self._tool_name,
            "arguments": {self._code_arg: prompt},
        })
        return self._extract_text(result)

    def ask_to_analyze(self, prompt: str) -> str:
        result = self._post("tools/call", {
            "name": self._tool_name_analyze,
            "arguments": {self._analyze_arg: prompt},
        })
        return self._extract_text(result)


class MyCodeClient(MCPClient):
    """Client for a running MyCode MCP server. Calls semantic tools directly."""

    def __init__(self, url: str = "http://localhost:8000/mcp", timeout: int = 120):
        self.url = url
        self._timeout = timeout
        self._session_id = None
        self._initialize()

    def analyze_codebase(self, path: str, save_to: str | None = None) -> dict:
        args = {"path": path}
        if save_to:
            args["save_to"] = save_to
        result = self._post("tools/call", {"name": "analyze_codebase", "arguments": args})
        return json.loads(self._extract_text(result))

    def generate_code(self, task: str, profile: dict | None = None, profile_path: str | None = None) -> str:
        args = {"task": task}
        if profile is not None:
            args["profile"] = profile
        elif profile_path:
            args["profile_path"] = profile_path
        result = self._post("tools/call", {"name": "generate_code", "arguments": args})
        return self._extract_text(result)
