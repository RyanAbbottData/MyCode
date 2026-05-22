from .base import AIBackend
from ..ricky_client import RickyClient


class RickyBackend(AIBackend):
    max_file_chars: int = 1500

    def __init__(self, url: str = "http://localhost:8000/mcp"):
        self._client = RickyClient(url=url)

    def ask_for_code(self, prompt: str) -> str:
        return self._client.ask_for_code(prompt)

    def ask_to_analyze(self, prompt: str) -> str:
        return self._client.ask_to_analyze(prompt)
