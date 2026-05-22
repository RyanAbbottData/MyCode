"""
Style-aware code generation agent.

Usage:
  my-code [--backend llama|claude|openai] analyze <dir>
  my-code [--backend llama|claude|openai] --api-key <key> generate "<task>"
"""

import argparse
import json
import sys
from pathlib import Path

from .analyzer import StyleAnalyzer
from .backends import make_backend
from .generator import generate_code

DEFAULT_PROFILE = Path("style_profile.json")


def cmd_analyze(args):
    root = Path(args.codebase).resolve()
    if not root.exists():
        sys.exit(f"Error: directory not found: {root}")

    backend = make_backend(
        backend=args.backend,
        api_key=args.api_key,
        ricky_url=args.ricky_url,
        mcp_url=args.mcp_url,
        model=args.model,
    )

    print(f"Analyzing codebase at {root} ...")
    analyzer = StyleAnalyzer(backend)
    profile = analyzer.analyze_codebase(root, verbose=args.verbose)

    out = Path(args.profile)
    StyleAnalyzer.save_profile(profile, out)


def cmd_generate(args):
    profile_path = Path(args.profile)
    if not profile_path.exists():
        sys.exit(
            f"Error: style profile not found at {profile_path}. "
            "Run 'analyze' first."
        )

    backend = make_backend(
        backend=args.backend,
        api_key=args.api_key,
        ricky_url=args.ricky_url,
        mcp_url=args.mcp_url,
        model=args.model,
    )

    profile = json.loads(profile_path.read_text(encoding="utf-8"))

    print("Generating code ...\n")
    code = generate_code(task=args.task, backend=backend, profile=profile)
    print(code)


def main():
    parser = argparse.ArgumentParser(description="Style-aware code agent")
    parser.add_argument(
        "--backend", default="llama", choices=["llama", "claude", "openai", "mcp"],
        help="AI backend to use (default: llama)",
    )
    parser.add_argument("--api-key", default=None, help="API key (claude/openai); falls back to env var")
    parser.add_argument("--model", default=None, help="Override default model for claude/openai backends")
    parser.add_argument("--ricky-url", default="http://localhost:8000/mcp", help="Ricky MCP server URL (llama backend)")
    parser.add_argument("--mcp-url", default="http://localhost:8001/mcp", help="MCP server URL (mcp backend)")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))

    sub = parser.add_subparsers(dest="command", required=True)

    p_analyze = sub.add_parser("analyze", help="Analyze a codebase and save a style profile")
    p_analyze.add_argument("codebase", help="Path to the codebase directory")
    p_analyze.add_argument("-v", "--verbose", action="store_true")
    p_analyze.set_defaults(func=cmd_analyze)

    p_gen = sub.add_parser("generate", help="Generate code matching the saved style profile")
    p_gen.add_argument("task", help="Description of what to write")
    p_gen.set_defaults(func=cmd_generate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
