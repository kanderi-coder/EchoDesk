import unittest
from unittest.mock import Mock

from internet.internet import InternetEngine, SearchResult


class DummyLLM:
    def __init__(self, summary_prefix="Summarized:"):
        self.summary_prefix = summary_prefix

    def summarize(self, text):
        return f"{self.summary_prefix} {text}"


class FakeProvider:
    def __init__(self, summary=None, success=True, error=None):
        self._summary = summary
        self._success = success
        self._error = error

    def search(self, query, timeout):
        return SearchResult(success=self._success, summary=self._summary, error=self._error)


class TestInternetEngine(unittest.TestCase):
    def test_search_uses_llm_summary_when_available(self):
        provider = FakeProvider(summary="Original internet text.")
        engine = InternetEngine(providers=[provider], llm_engine=DummyLLM())

        response = engine.search("test query")
        self.assertEqual(response, "Summarized: Original internet text.")

    def test_search_returns_original_text_when_llm_unavailable(self):
        provider = FakeProvider(summary="Original internet text.")
        engine = InternetEngine(providers=[provider], llm_engine=None)

        response = engine.search("test query")
        self.assertEqual(response, "Original internet text.")

    def test_search_fallback_when_provider_fails(self):
        provider = FakeProvider(success=False, error="Provider failed")
        engine = InternetEngine(providers=[provider], llm_engine=DummyLLM())

        response = engine.search("test query")
        self.assertIn("I couldn't find a clear answer", response)
        self.assertIn("Provider failed", response)

    def test_search_with_empty_query_returns_fallback_message(self):
        provider = FakeProvider(summary="Should not matter")
        engine = InternetEngine(providers=[provider], llm_engine=DummyLLM())

        response = engine.search("")
        self.assertIn("I couldn't find a clear answer", response)

    def test_search_uses_llm_engine_to_summarize_successful_result(self):
        provider = FakeProvider(summary="Original internet text.")
        llm_engine = Mock(spec=["summarize"])
        llm_engine.summarize.return_value = "LLM summary result."
        engine = InternetEngine(providers=[provider], llm_engine=llm_engine)

        response = engine.search("test query")

        self.assertEqual(response, "LLM summary result.")
        llm_engine.summarize.assert_called_once_with("Original internet text.")

    def test_search_returns_original_summary_when_llm_engine_is_not_provided(self):
        provider = FakeProvider(summary="Original internet text.")
        engine = InternetEngine(providers=[provider], llm_engine=None)

        response = engine.search("test query")

        self.assertEqual(response, "Original internet text.")

    def test_search_returns_original_summary_when_llm_engine_raises(self):
        provider = FakeProvider(summary="Original internet text.")
        llm_engine = Mock(spec=["summarize"])
        llm_engine.summarize.side_effect = RuntimeError("LLM error")
        engine = InternetEngine(providers=[provider], llm_engine=llm_engine)

        response = engine.search("test query")

        self.assertEqual(response, "Original internet text.")
        llm_engine.summarize.assert_called_once_with("Original internet text.")

    def test_search_returns_original_summary_when_llm_engine_returns_invalid_summary(self):
        provider = FakeProvider(summary="Original internet text.")
        llm_engine = Mock(spec=["summarize"])
        llm_engine.summarize.return_value = "   "
        engine = InternetEngine(providers=[provider], llm_engine=llm_engine)

        response = engine.search("test query")

        self.assertEqual(response, "Original internet text.")
        llm_engine.summarize.assert_called_once_with("Original internet text.")


if __name__ == "__main__":
    unittest.main()
