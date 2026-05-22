from abc import ABC, abstractmethod


class AIBackend(ABC):
    max_file_chars: int = 6000

    @abstractmethod
    def ask_for_code(self, prompt: str) -> str:
        pass

    @abstractmethod
    def ask_to_analyze(self, prompt: str) -> str:
        pass