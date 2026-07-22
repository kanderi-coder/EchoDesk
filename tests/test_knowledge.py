import unittest

from knowledge.knowledge import KnowledgeEngine


class TestKnowledgeEngine(unittest.TestCase):
    def test_known_answer_returns_local_fact(self):
        engine = KnowledgeEngine()
        answer = engine.search("who invented python")

        self.assertIsInstance(answer, str)
        self.assertIn("Guido van Rossum", answer)

    def test_unknown_answer_returns_none(self):
        engine = KnowledgeEngine()
        answer = engine.search("what is the capital of lisp")

        self.assertIsNone(answer)


if __name__ == "__main__":
    unittest.main()
