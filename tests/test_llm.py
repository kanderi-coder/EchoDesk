import json
import socket
import unittest
from io import BytesIO
from urllib.error import URLError
from unittest.mock import patch

from llm.engine import LLMEngine
from llm.ollama_provider import OllamaProvider
from llm.provider import BaseLLMProvider


class DummyProvider(BaseLLMProvider):
    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return f"Echo: {prompt}"


class FakeResponse:
    def __init__(self, data: bytes, status=200):
        self._data = data
        self.status = status

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class TestLLMEngine(unittest.TestCase):
    def test_ask_delegates_to_provider(self):
        provider = DummyProvider()
        engine = LLMEngine(provider)

        response = engine.ask("Hello")

        self.assertEqual(response, "Echo: " + provider.prompts[0])

    def test_summarize_delegates_to_provider(self):
        provider = DummyProvider()
        engine = LLMEngine(provider)
        response = engine.summarize("Some long text.")

        self.assertIn("Some long text.", provider.prompts[0])
        self.assertTrue(response.startswith("Echo:"))

    def test_explain_delegates_to_provider(self):
        provider = DummyProvider()
        engine = LLMEngine(provider)
        response = engine.explain("Explain this")

        self.assertIn("Explain this", provider.prompts[0])
        self.assertTrue(response.startswith("Echo:"))

    def test_reason_delegates_to_provider(self):
        provider = DummyProvider()
        engine = LLMEngine(provider)
        response = engine.reason("Why?", "Because")

        self.assertIn("Why?", provider.prompts[0])
        self.assertIn("Because", provider.prompts[0])
        self.assertTrue(response.startswith("Echo:"))


class TestOllamaProvider(unittest.TestCase):
    @patch("llm.ollama_provider.urlopen")
    def test_generate_returns_response_text(self, mock_urlopen):
        payload = json.dumps({"text": "hello"}).encode("utf-8")
        mock_urlopen.return_value = FakeResponse(payload)

        provider = OllamaProvider()
        output = provider.generate("test prompt")

        self.assertEqual(output, "hello")

    @patch("llm.ollama_provider.urlopen")
    def test_generate_handles_invalid_json(self, mock_urlopen):
        payload = b"not json"
        mock_urlopen.return_value = FakeResponse(payload)

        provider = OllamaProvider()
        output = provider.generate("test prompt")

        self.assertIn("invalid JSON", output)

    @patch("llm.ollama_provider.urlopen")
    def test_generate_handles_timeout(self, mock_urlopen):
        mock_urlopen.side_effect = URLError(socket.timeout("timed out"))

        provider = OllamaProvider()
        output = provider.generate("test prompt")

        self.assertIn("timeout error", output.lower())

    @patch("llm.ollama_provider.urlopen")
    def test_generate_handles_connection_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("connection refused")

        provider = OllamaProvider()
        output = provider.generate("test prompt")

        self.assertIn("connection error", output.lower())


if __name__ == "__main__":
    unittest.main()
