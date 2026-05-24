from abc import ABC, abstractmethod


class AIBackend(ABC):
    max_file_chars: int = 6000

    @abstractmethod
    def ask_for_code(self, prompt: str) -> str:
        pass

    @abstractmethod
    def ask_to_analyze(self, prompt: str, fallback_prompt: str | None = None) -> str:
        """Analyze code style and return a JSON string.

        Args:
            prompt: Full-detail analysis prompt.
            fallback_prompt: Simpler prompt used when the backend cannot enforce
                JSON output constraints (e.g. local servers that reject response_format).
        """
        pass