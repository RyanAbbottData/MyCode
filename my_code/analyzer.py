import ast
import json
import re
from pathlib import Path

from .backends import AIBackend

_SKIP_EXACT = {"__pycache__", ".git", "node_modules", "dist", "build"}


def _should_skip(path: Path) -> bool:
    return any(
        part in _SKIP_EXACT or "venv" in part
        for part in path.parts
    )


def _collect_python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if not _should_skip(p))


def _repair_json(text: str) -> dict:
    """Extract and repair JSON from an LLM response using progressive fallbacks."""
    # Strategy 1: direct parse (fast path for well-behaved models)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Strategy 2: extract from markdown code fence ```json ... ```
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fence.group(1) if fence else None

    # Strategy 3: find bare {...} block in prose
    if candidate is None:
        obj = re.search(r"\{.*\}", text, re.DOTALL)
        if obj is None:
            raise ValueError(f"No JSON found in response:\n{text[:300]}")
        candidate = obj.group()

    # Strategy 4: ast.literal_eval handles single-quoted dicts and Python constants
    try:
        result = ast.literal_eval(candidate)
        if isinstance(result, dict):
            return result
    except (ValueError, SyntaxError):
        pass

    # Strategy 5: Python constants → JSON equivalents, strip trailing commas
    fixed = re.sub(r'\bTrue\b',  'true',  candidate)
    fixed = re.sub(r'\bFalse\b', 'false', fixed)
    fixed = re.sub(r'\bNone\b',  'null',  fixed)
    fixed = re.sub(r',\s*([}\]])', r'\1', fixed)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Strategy 6: single-quote → double-quote (safe for enum-like style values)
    return json.loads(fixed.replace("'", '"'))


class StyleAnalyzer:
    def __init__(self, backend: AIBackend):
        self.backend = backend

    def analyze_file(self, path: Path) -> dict:
        source = path.read_text(encoding="utf-8", errors="ignore")[:self.backend.max_file_chars]
        if not source.strip():
            return {}
        prompt = self.backend.extraction_prompt_template.format(filename=path.name, source=source)
        raw = self.backend.ask_to_analyze(prompt)
        try:
            return _repair_json(raw)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"  [warn] Could not parse style from {path.name}: {e}")
            return {}

    def analyze_codebase(self, root: Path, verbose: bool = False) -> dict:
        files = _collect_python_files(root)
        if not files:
            raise FileNotFoundError(f"No Python files found under {root}")

        profile = {}
        for path in files:
            rel = path.relative_to(root)
            if verbose:
                print(f"  Analyzing {rel} ...")
            obs = self.analyze_file(path)
            if not obs:
                continue
            if not profile:
                profile = obs
                continue
            prompt = self.backend.merge_prompt_template.format(
                profile=json.dumps(profile, indent=2),
                observation=json.dumps(obs, indent=2),
                filename=path.name,
            )
            raw = self.backend.ask_to_analyze(prompt)
            try:
                profile = _repair_json(raw)
            except (ValueError, json.JSONDecodeError) as e:
                print(f"  [warn] Could not merge style from {path.name}: {e}")

        if not profile:
            raise RuntimeError("No style data could be extracted from any file.")

        return profile

    @staticmethod
    def save_profile(profile: dict, path: Path):
        path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
        print(f"Style profile saved to {path}")

    @staticmethod
    def load_profile(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))
