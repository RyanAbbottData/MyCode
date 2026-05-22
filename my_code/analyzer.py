import json
import re
from pathlib import Path

from .backends import AIBackend
from .utils.prompts import STYLE_EXTRACTION_PROMPT, STYLE_SUMMARY_PROMPT

_SKIP_EXACT = {"__pycache__", ".git", "node_modules", "dist", "build"}


def _should_skip(path: Path) -> bool:
    return any(
        part in _SKIP_EXACT or "venv" in part
        for part in path.parts
    )


def _collect_python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if not _should_skip(p))


def _extract_json(text: str) -> dict:
    # Claude/OpenAI return clean JSON; llama wraps it in prose
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in response:\n{text[:300]}")
    return json.loads(match.group())


class StyleAnalyzer:
    def __init__(self, backend: AIBackend):
        self.backend = backend

    def analyze_file(self, path: Path) -> dict:
        source = path.read_text(encoding="utf-8", errors="ignore")[:self.backend.max_file_chars]
        if not source.strip():
            return {}
        prompt = STYLE_EXTRACTION_PROMPT.format(filename=path.name, source=source)
        raw = self.backend.ask_to_analyze(prompt)
        try:
            return _extract_json(raw)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"  [warn] Could not parse style from {path.name}: {e}")
            return {}

    def analyze_codebase(self, root: Path, verbose: bool = False) -> dict:
        files = _collect_python_files(root)
        if not files:
            raise FileNotFoundError(f"No Python files found under {root}")

        observations = []
        for path in files:
            rel = path.relative_to(root)
            if verbose:
                print(f"  Analyzing {rel} ...")
            obs = self.analyze_file(path)
            if obs:
                observations.append(obs)

        if not observations:
            raise RuntimeError("No style data could be extracted from any file.")

        if len(observations) == 1:
            return observations[0]

        prompt = STYLE_SUMMARY_PROMPT.format(
            observations=json.dumps(observations, indent=2)
        )
        raw = self.backend.ask_to_analyze(prompt)
        try:
            return _extract_json(raw)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"[warn] Could not synthesize profile, using first observation: {e}")
            return observations[0]

    @staticmethod
    def save_profile(profile: dict, path: Path):
        path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
        print(f"Style profile saved to {path}")

    @staticmethod
    def load_profile(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))
