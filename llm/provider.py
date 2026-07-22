from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Base interface for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a response from the provider for the given prompt."""
        raise NotImplementedError
