__version__ = "0.6.0"

from .analyzer import StyleAnalyzer
from .generator import generate_code
from .backends import AIBackend, ClaudeBackend, OpenAIBackend, MCPBackend, make_backend
from .server import MCPServer


def run_server(backend=None, host: str = "127.0.0.1", port: int = 8080):
    """Start a blocking MCP server exposing analyze_codebase and generate_code as tools."""
    MCPServer(backend or make_backend(), host=host, port=port).run()


__all__ = [
    "StyleAnalyzer",
    "generate_code",
    "AIBackend",
    "ClaudeBackend",
    "OpenAIBackend",
    "MCPBackend",
    "make_backend",
    "MCPServer",
    "run_server",
]
