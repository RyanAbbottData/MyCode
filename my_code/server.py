import json
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .analyzer import StyleAnalyzer
from .generator import generate_code as _generate_code

_PROTOCOL = "2024-11-05"

_TOOLS = [
    {
        "name": "analyze_codebase",
        "description": "Analyze a codebase directory and extract its coding style profile.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the codebase directory to analyze.",
                },
                "save_to": {
                    "type": "string",
                    "description": "Optional path to save the resulting profile JSON file.",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "generate_code",
        "description": "Generate Python code that matches a saved style profile.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Description of what code to write.",
                },
                "profile": {
                    "type": "object",
                    "description": "Inline style profile object — takes precedence over profile_path.",
                },
                "profile_path": {
                    "type": "string",
                    "description": "Path to a saved style_profile.json (default: style_profile.json).",
                },
            },
            "required": ["task"],
        },
    },
]


class _MCPError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class _MCPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/mcp":
            self._send_sse({"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Not found"}}, 404)
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            msg = json.loads(body)
        except json.JSONDecodeError:
            self._send_sse({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}, 400)
            return

        req_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        try:
            result, extra_headers = self.server.mcp._handle(method, params)
            self._send_sse({"jsonrpc": "2.0", "id": req_id, "result": result}, 200, extra_headers)
        except _MCPError as e:
            self._send_sse({"jsonrpc": "2.0", "id": req_id, "error": {"code": e.code, "message": e.message}}, 200)
        except Exception as e:
            self._send_sse({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}}, 200)

    def _send_sse(self, data: dict, status: int = 200, extra_headers: dict | None = None):
        body = f"data: {json.dumps(data)}\n\n".encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(body)))
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


class MCPServer:
    def __init__(self, backend, host: str = "127.0.0.1", port: int = 8080, default_profile: str = "style_profile.json"):
        self._backend = backend
        self._host = host
        self._port = port
        self._default_profile = default_profile

    def _handle(self, method: str, params: dict) -> tuple[dict, dict | None]:
        if method == "initialize":
            return self._initialize(), {"Mcp-Session-Id": str(uuid.uuid4())}
        if method == "tools/list":
            return {"tools": _TOOLS}, None
        if method == "tools/call":
            name = params.get("name", "")
            arguments = params.get("arguments", {})
            text = self._call_tool(name, arguments)
            return {"content": [{"type": "text", "text": text}]}, None
        raise _MCPError(-32601, f"Method not found: {method}")

    def _initialize(self) -> dict:
        return {
            "protocolVersion": _PROTOCOL,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "mycode", "version": "0.3.0"},
        }

    def _call_tool(self, name: str, args: dict) -> str:
        if name == "analyze_codebase":
            return self._analyze(args)
        if name == "generate_code":
            return self._generate(args)
        raise _MCPError(-32602, f"Unknown tool: {name}")

    def _analyze(self, args: dict) -> str:
        path = Path(args["path"]).resolve()
        profile = StyleAnalyzer(self._backend).analyze_codebase(path)
        save_to = args.get("save_to")
        if save_to:
            StyleAnalyzer.save_profile(profile, Path(save_to))
        return json.dumps(profile, indent=2)

    def _generate(self, args: dict) -> str:
        task = args["task"]
        profile = args.get("profile")
        if profile is None:
            profile_path = Path(args.get("profile_path") or self._default_profile)
            profile = StyleAnalyzer.load_profile(profile_path)
        return _generate_code(task=task, backend=self._backend, profile=profile)

    def start(self) -> ThreadingHTTPServer:
        httpd = ThreadingHTTPServer((self._host, self._port), _MCPRequestHandler)
        httpd.mcp = self
        return httpd

    def run(self):
        httpd = self.start()
        host, port = httpd.server_address
        print(f"MyCode MCP server running at http://{host}:{port}/mcp")
        print(f'Add to your MCP config:  {{"mycode": {{"url": "http://{host}:{port}/mcp"}}}}')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()
