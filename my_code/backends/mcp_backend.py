from .base import AIBackend

_MSG = "MCPBackend is not yet configured. Set the MCP server URL and implement this backend."


class MCPBackend(AIBackend):
    def __init__(self, url: str = "http://localhost:8001/mcp"):
        self.url = url

    def ask_for_code(self, prompt: str) -> str:
        raise NotImplementedError(_MSG)

    def ask_to_analyze(self, prompt: str) -> str:
        raise NotImplementedError(_MSG)
