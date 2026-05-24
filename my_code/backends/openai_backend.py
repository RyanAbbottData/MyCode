from .base import AIBackend


class OpenAIBackend(AIBackend):
    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str | None = None, timeout: int = 600):
        """
        Args:
            timeout: HTTP timeout in seconds for each LLM call. Local models may need 600+.
        """
        try:
            import openai
        except ImportError:
            raise ImportError("OpenAI backend requires 'openai': pip install 'my-code[openai]'")
        client_kwargs = {"api_key": api_key, "timeout": timeout}
        if base_url is not None:
            client_kwargs["base_url"] = base_url
        self._client = openai.OpenAI(**client_kwargs)
        self._model = model

    def _call(self, system: str, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=2048,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content

    def ask_for_code(self, prompt: str) -> str:
        return self._call(
            "You are an expert Python developer. Return only Python code, no explanation.",
            prompt,
        )

    def ask_to_analyze(self, prompt: str) -> str:
        return self._call(
            "You are a code style analyst. Return only valid JSON, no explanation.",
            prompt,
        )
