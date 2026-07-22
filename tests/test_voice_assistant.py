import unittest
from unittest.mock import MagicMock

from voice.assistant import VoiceAssistant
from voice.controller import VoiceController


class TestVoiceAssistant(unittest.TestCase):
    def test_listen_returns_error_when_unavailable(self):
        mock_recognizer = MagicMock()
        mock_recognizer.available.return_value = {"success": False, "message": "No mic"}
        assistant = VoiceAssistant(recognizer=mock_recognizer, synthesizer=MagicMock(), brain=MagicMock())

        result = assistant.listen()

        self.assertFalse(result["success"])
        self.assertEqual(result["stage"], "available")

    def test_process_command_returns_response(self):
        mock_recognizer = MagicMock()
        mock_recognizer.recognize.return_value = {
            "success": True,
            "result": {"text": "open chrome"},
        }
        mock_brain = MagicMock()
        mock_brain.process.return_value = "Opening Chrome"
        assistant = VoiceAssistant(recognizer=mock_recognizer, synthesizer=MagicMock(), brain=mock_brain)

        result = assistant.process_command()

        self.assertTrue(result["success"])
        self.assertEqual(result["command"], "open chrome")
        self.assertEqual(result["response"], "Opening Chrome")

    def test_respond_speaks_response(self):
        mock_synthesizer = MagicMock()
        mock_synthesizer.speak.return_value = {"success": True}
        assistant = VoiceAssistant(recognizer=MagicMock(), synthesizer=mock_synthesizer, brain=MagicMock())

        result = assistant.respond("Hello world")

        self.assertTrue(result["success"])
        mock_synthesizer.speak.assert_called_once_with("Hello world")

    def test_run_once_completes_full_cycle(self):
        mock_recognizer = MagicMock()
        mock_recognizer.available.return_value = {"success": True}
        mock_recognizer.listen.return_value = {"success": True}
        mock_recognizer.recognize.return_value = {
            "success": True,
            "result": {"text": "hello"},
        }
        mock_brain = MagicMock()
        mock_brain.process.return_value = "Hi there"
        mock_synthesizer = MagicMock()
        mock_synthesizer.speak.return_value = {"success": True}

        assistant = VoiceAssistant(
            recognizer=mock_recognizer,
            synthesizer=mock_synthesizer,
            brain=mock_brain,
        )

        result = assistant.run_once()

        self.assertTrue(result["success"])
        self.assertEqual(result["command"], "hello")
        self.assertEqual(result["response"], "Hi there")
        mock_synthesizer.speak.assert_called_once_with("Hi there")

    def test_run_once_stops_on_recognition_failure(self):
        mock_recognizer = MagicMock()
        mock_recognizer.available.return_value = {"success": True}
        mock_recognizer.listen.return_value = {"success": True}
        mock_recognizer.recognize.return_value = {"success": False, "message": "Could not understand"}
        assistant = VoiceAssistant(recognizer=mock_recognizer, synthesizer=MagicMock(), brain=MagicMock())

        result = assistant.run_once()

        self.assertFalse(result["success"])
        self.assertEqual(result["stage"], "recognize")


class TestVoiceControllerAssistantIntegration(unittest.TestCase):
    def test_run_voice_command_delegates_to_assistant(self):
        mock_assistant = MagicMock()
        mock_assistant.run_once.return_value = {"success": True, "command": "hi"}
        controller = VoiceController(assistant=mock_assistant)

        result = controller.run_voice_command()

        mock_assistant.run_once.assert_called_once()
        self.assertTrue(result["success"])
        self.assertEqual(result["command"], "hi")


if __name__ == "__main__":
    unittest.main()
