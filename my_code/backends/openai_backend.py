from .base import AIBackend


class OpenAIBackend(AIBackend):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        try:
            import openai
        except ImportError:
            raise ImportError("OpenAI backend requires 'openai': pip install 'my-code[openai]'")
        self._client = openai.OpenAI(api_key=api_key)
        self._model = model

    def _call(self, system: str, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
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
