from .base import AIBackend
from ..mcp_client import MCPClient


class MCPBackend(AIBackend):
    def __init__(self, url: str = "http://localhost:8001/mcp", timeout: int = 120):
        self._client = MCPClient(url=url, timeout=timeout)

    def ask_for_code(self, prompt: str) -> str:
        return self._client.ask_for_code(prompt)

    def ask_to_analyze(self, prompt: str) -> str:
        return self._client.ask_to_analyze(prompt)
