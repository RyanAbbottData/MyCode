from .base import AIBackend


class ClaudeBackend(AIBackend):
    def __init__(self, api_key: str, model: str = "claude-opus-4-7"):
        try:
            import anthropic
        except ImportError:
            raise ImportError("Claude backend requires 'anthropic': pip install 'my-code[claude]'")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def _call(self, system: str, prompt: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def ask_for_code(self, prompt: str) -> str:
        return self._call(
            "You are an expert Python developer. Return only Python code, no explanation.",
            prompt,
        )

    def ask_to_analyze(self, prompt: str, fallback_prompt: str | None = None) -> str:
        """Request code style analysis as JSON. fallback_prompt is unused (Claude follows instructions reliably)."""
        return self._call(
            "You are a code style analyst. Return only valid JSON, no explanation.",
            prompt,
        )
