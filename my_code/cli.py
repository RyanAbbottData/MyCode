"""
Style-aware code generation agent.

Usage:
  my-code [--backend claude|openai|local|mcp] analyze <dir>
  my-code [--backend claude|openai|local|mcp] --api-key <key> generate "<task>"
"""

import argparse
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

from .analyzer import StyleAnalyzer
from .backends import make_backend
from .generator import generate_code
from .mcp_client import MyCodeClient
from .server import MCPServer

DEFAULT_PROFILE = Path("style_profile.json")


def cmd_analyze(args):
    root = Path(args.codebase).resolve()
    if not root.exists():
        sys.exit(f"Error: directory not found: {root}")

    if args.backend == "mcp":
        client = MyCodeClient(args.mcp_url, args.timeout)
        print(f"Analyzing codebase at {root} via MyCode server ...")
        profile = client.analyze_codebase(str(root))
        StyleAnalyzer.save_profile(profile, Path(args.profile))
        return

    backend = make_backend(
        backend=args.backend,
        api_key=args.api_key,
        mcp_url=args.mcp_url,
        llm_url=args.llm_url,
        model=args.model,
        timeout=args.timeout,
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

    if args.backend == "mcp":
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        client = MyCodeClient(args.mcp_url, args.timeout)
        print("Generating code ...\n")
        print(client.generate_code(args.task, profile=profile))
        return

    backend = make_backend(
        backend=args.backend,
        api_key=args.api_key,
        mcp_url=args.mcp_url,
        llm_url=args.llm_url,
        model=args.model,
        timeout=args.timeout,
    )

    profile = json.loads(profile_path.read_text(encoding="utf-8"))

    print("Generating code ...\n")
    code = generate_code(task=args.task, backend=backend, profile=profile)
    print(code)


def _spawn_daemon(args):
    cmd = [
        sys.executable, "-m", "my_code",
        "--backend", args.backend,
        "--mcp-url", args.mcp_url,
        "--llm-url", args.llm_url,
        "--timeout", str(args.timeout),
        "--profile", args.profile,
        "serve",
        "--host", args.host,
        "--port", str(args.port),
    ]
    if args.api_key:
        cmd += ["--api-key", args.api_key]
    if args.model:
        cmd += ["--model", args.model]

    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(cmd, **kwargs)
    Path(args.pid_file).write_text(str(proc.pid))
    print(f"MyCode MCP server started as daemon (PID {proc.pid}) at http://{args.host}:{args.port}/mcp")
    print(f"Stop with: my-code stop --pid-file {args.pid_file}")


def cmd_stop(args):
    pid_file = Path(args.pid_file)
    pid = int(pid_file.read_text().strip())
    os.kill(pid, signal.SIGTERM)
    pid_file.unlink()
    print(f"MyCode MCP server (PID {pid}) stopped.")


def cmd_serve(args):
    if args.daemon:
        _spawn_daemon(args)
        return
    backend = make_backend(
        backend=args.backend,
        api_key=args.api_key,
        mcp_url=args.mcp_url,
        llm_url=args.llm_url,
        model=args.model,
        timeout=args.timeout,
    )
    MCPServer(backend, host=args.host, port=args.port, default_profile=args.profile).run()


def main():
    parser = argparse.ArgumentParser(description="Style-aware code agent")
    parser.add_argument(
        "--backend", default="claude", choices=["claude", "openai", "local", "mcp"],
        help="AI backend to use (default: claude)",
    )
    parser.add_argument("--api-key", default=None, help="API key (claude/openai); falls back to env var")
    parser.add_argument("--model", default=None, help="Override default model for claude/openai/local backends")
    parser.add_argument("--mcp-url", default="http://localhost:8001/mcp", help="MyCode MCP server URL (mcp backend)")
    parser.add_argument("--llm-url", default="http://localhost:8080/v1", help="Base URL of a local OpenAI-compatible LLM server (local backend)")
    parser.add_argument("--timeout", type=int, default=120, help="Request timeout in seconds (default: 120)")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))

    sub = parser.add_subparsers(dest="command", required=True)

    p_analyze = sub.add_parser("analyze", help="Analyze a codebase and save a style profile")
    p_analyze.add_argument("codebase", help="Path to the codebase directory")
    p_analyze.add_argument("-v", "--verbose", action="store_true")
    p_analyze.set_defaults(func=cmd_analyze)

    p_gen = sub.add_parser("generate", help="Generate code matching the saved style profile")
    p_gen.add_argument("task", help="Description of what to write")
    p_gen.set_defaults(func=cmd_generate)

    p_serve = sub.add_parser("serve", help="Start an MCP server exposing analyze and generate as tools")
    p_serve.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    p_serve.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    p_serve.add_argument("--daemon", action="store_true", help="Run server as a detached background process")
    p_serve.add_argument("--pid-file", default="mycode.pid", help="PID file path when running as daemon (default: mycode.pid)")
    p_serve.set_defaults(func=cmd_serve)

    p_stop = sub.add_parser("stop", help="Stop a running daemon server")
    p_stop.add_argument("--pid-file", default="mycode.pid", help="PID file written by 'serve --daemon' (default: mycode.pid)")
    p_stop.set_defaults(func=cmd_stop)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
