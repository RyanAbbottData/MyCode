import os

from .base import AIBackend
from .claude_backend import ClaudeBackend
from .openai_backend import OpenAIBackend
from .mcp_backend import MCPBackend

__all__ = ["AIBackend", "ClaudeBackend", "OpenAIBackend", "MCPBackend", "make_backend"]


def make_backend(
    backend: str = "claude",
    api_key: str | None = None,
    mcp_url: str = "http://localhost:8001/mcp",
    model: str | None = None,
    timeout: int = 120,
) -> AIBackend:
    if backend == "claude":
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("Claude backend requires ANTHROPIC_API_KEY or --api-key")
        return ClaudeBackend(api_key=key, **{"model": model} if model else {})
    if backend == "openai":
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError("OpenAI backend requires OPENAI_API_KEY or --api-key")
        return OpenAIBackend(api_key=key, **{"model": model} if model else {})
    if backend == "mcp":
        return MCPBackend(url=mcp_url, timeout=timeout)
    raise ValueError(f"Unknown backend {backend!r}. Choose: claude, openai, mcp")
