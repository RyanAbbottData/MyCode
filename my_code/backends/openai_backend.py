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


class LocalBackend(OpenAIBackend):
    """OpenAI-compatible local LLM with optional explicit instruction formatting.

    Use prompt_format='llama2' when the local server does not apply the model's
    chat template automatically (e.g. llama.cpp without --chat-template).
    """

    _FORMATS = {
        "llama2": "<s>[INST] <<SYS>>\n{system}\n<</SYS>>\n\n{prompt} [/INST]",
    }

    def __init__(self, *args, prompt_format: str = "openai", **kwargs):
        """
        Args:
            prompt_format: 'openai' uses standard chat roles; 'llama2' wraps in [INST]/[/INST].
        """
        super().__init__(*args, **kwargs)
        self._prompt_format = prompt_format

    def _call(self, system: str, prompt: str) -> str:
        if self._prompt_format == "openai":
            return super()._call(system, prompt)
        template = self._FORMATS[self._prompt_format]
        combined = template.format(system=system, prompt=prompt)
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=2048,
            messages=[{"role": "user", "content": combined}],
        )
        return response.choices[0].message.content
