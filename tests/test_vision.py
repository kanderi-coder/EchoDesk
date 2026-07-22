import unittest

from llm.engine import LLMEngine
from agent.context import AgentContext
from vision.analyzer import ScreenAnalyzer
from vision.screen_context import ScreenContext


class DummyLLM:
    def explain(self, prompt: str) -> str:
        return "This is a mock explanation based on the screen content."


class TestVisionAnalyzer(unittest.TestCase):
    def test_detects_application_and_errors(self):
        analyzer = ScreenAnalyzer(llm_engine=None)
        text = "Visual Studio Code - project | File Edit View" + "\n" + "Traceback (most recent call last): ImportError: No module named foo"
        context = analyzer.build_context(text)

        self.assertEqual(context.application, "Visual Studio Code")
        self.assertEqual(context.window_title, "Visual Studio Code - project | File Edit View")
        self.assertIn("Top menu", context.sections)
        self.assertIn("traceback", context.errors)
        self.assertIn("importerror", context.errors)
        self.assertEqual(context.language, "English")

    def test_analyze_uses_llm_when_available(self):
        analyzer = ScreenAnalyzer(llm_engine=DummyLLM())
        text = "Firefox - example.com | Error 404 Not Found"
        result = analyzer.analyze(text)

        self.assertEqual(result, "This is a mock explanation based on the screen content.")

    def test_analyze_returns_structured_summary_when_llm_unavailable(self):
        analyzer = ScreenAnalyzer(llm_engine=None)
        text = "Google Chrome | File Edit View" + "\n" + "Warning: Something may be wrong."
        result = analyzer.analyze(text)

        self.assertIn("Application: Google Chrome", result)
        self.assertIn("Visible screen text preview:", result)

    def test_detect_language_estimation(self):
        analyzer = ScreenAnalyzer(llm_engine=None)
        spanish_text = "Hola, gracias por tu ayuda"
        self.assertEqual(analyzer.detect_language(spanish_text), "Spanish")

        french_text = "Bonjour, merci beaucoup"
        self.assertEqual(analyzer.detect_language(french_text), "French")

        chinese_text = "你好，世界"
        self.assertEqual(analyzer.detect_language(chinese_text), "Chinese")

        russian_text = "Привет мир"
        self.assertEqual(analyzer.detect_language(russian_text), "Russian")

    def test_detect_buttons_and_menus(self):
        analyzer = ScreenAnalyzer(llm_engine=None)
        text = "OK Cancel Save File Edit View Home Insert"
        context = analyzer.build_context(text)

        self.assertIn("OK", context.buttons)
        self.assertIn("Cancel", context.buttons)
        self.assertIn("Top menu", context.menus)


if __name__ == "__main__":
    unittest.main()
