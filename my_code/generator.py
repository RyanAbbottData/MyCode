import json

from .backends.base import AIBackend
from .utils.prompts import CODE_GENERATION_PROMPT


def generate_code(task: str, backend: AIBackend, profile: dict) -> str:
    """Generate Python code matching the given style profile."""
    prompt = CODE_GENERATION_PROMPT.format(
        style_profile=json.dumps(profile, indent=2),
        task=task,
    )
    return backend.ask_for_code(prompt)
