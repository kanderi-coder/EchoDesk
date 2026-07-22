import json
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .provider import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    """Provider for Ollama local LLM serving via HTTP."""

    def __init__(self, model: str = "llama3.2", endpoint: str = "http://localhost:11434/api/generate", timeout: int = 15):
        self.model = model
        self.endpoint = endpoint
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        """Generate a response from the Ollama server for the given prompt."""
        payload = json.dumps({"model": self.model, "prompt": prompt}).encode("utf-8")
        request = Request(self.endpoint, data=payload, headers={"Content-Type": "application/json"}, method="POST")

        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                text = raw.decode("utf-8")
                parsed = json.loads(text)

                if isinstance(parsed, dict):
                    if "text" in parsed and isinstance(parsed["text"], str):
                        return parsed["text"]
                    if "results" in parsed and isinstance(parsed["results"], list) and parsed["results"]:
                        first = parsed["results"][0]
                        if isinstance(first, dict) and "output" in first and isinstance(first["output"], str):
                            return first["output"]

                return "OllamaProvider error: unexpected response format from server"
        except HTTPError as error:
            return f"OllamaProvider HTTP error {error.code}: {error.reason}"
        except URLError as error:
            if isinstance(error.reason, socket.timeout):
                return "OllamaProvider timeout error: server did not respond in time"
            return f"OllamaProvider connection error: {error.reason}"
        except socket.timeout:
            return "OllamaProvider timeout error: server did not respond in time"
        except json.JSONDecodeError as error:
            return f"OllamaProvider invalid JSON response: {error}"
        except Exception as error:
            return f"OllamaProvider unexpected error: {error}"
