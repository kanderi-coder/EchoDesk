import unittest
from unittest.mock import MagicMock

from voice.controller import VoiceController
from voice.speech_recognizer import SpeechRecognizer


class TestSpeechRecognizer(unittest.TestCase):
    def test_initialize_returns_error_when_library_missing(self):
        recognizer = SpeechRecognizer(sr_module=None)

        result = recognizer.initialize()

        self.assertFalse(result["success"])
        self.assertIn("Speech recognition library is unavailable", result["message"])

    def test_available_returns_success_with_microphone(self):
        mock_microphone = MagicMock()
        mock_microphone.list_microphone_names = MagicMock(return_value=["Microphone 1"])

        mock_sr = MagicMock(Microphone=mock_microphone)
        recognizer = SpeechRecognizer(sr_module=mock_sr)

        result = recognizer.available()

        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["device_count"], 1)

    def test_listen_and_recognize_return_text_when_successful(self):
        mock_source = MagicMock()
        mock_microphone = MagicMock()
        mock_microphone.__enter__.return_value = mock_source
        mock_microphone.__exit__.return_value = None
        mock_microphone.list_microphone_names = MagicMock(return_value=["Mic"])

        mock_recognizer_instance = MagicMock()
        mock_recognizer_instance.listen.return_value = "audio_data"
        mock_recognizer_instance.recognize_google.return_value = "open chrome"

        mock_sr = MagicMock()
        mock_sr.Microphone = MagicMock(return_value=mock_microphone)
        mock_sr.Recognizer = MagicMock(return_value=mock_recognizer_instance)

        recognizer = SpeechRecognizer(sr_module=mock_sr)
        listen_result = recognizer.listen()
        self.assertTrue(listen_result["success"])

        recognize_result = recognizer.recognize()
        self.assertTrue(recognize_result["success"])
        self.assertEqual(recognize_result["result"]["text"], "open chrome")
        mock_recognizer_instance.listen.assert_called_once_with(mock_source)
        mock_recognizer_instance.recognize_google.assert_called_once_with("audio_data")

    def test_recognize_without_listen_returns_error(self):
        mock_sr = MagicMock()
        recognizer = SpeechRecognizer(sr_module=mock_sr)
        recognizer.recognizer = MagicMock()

        result = recognizer.recognize()

        self.assertFalse(result["success"])
        self.assertIn("Call listen() first", result["message"])

    def test_listen_failure_returns_error(self):
        mock_microphone = MagicMock()
        mock_microphone.__enter__.side_effect = RuntimeError("Mic unavailable")
        mock_microphone.__exit__.return_value = None

        mock_sr = MagicMock()
        mock_sr.Microphone = MagicMock(return_value=mock_microphone)
        mock_sr.Recognizer = MagicMock(return_value=MagicMock())

        recognizer = SpeechRecognizer(sr_module=mock_sr)
        result = recognizer.listen()

        self.assertFalse(result["success"])
        self.assertIn("Failed to capture microphone input", result["message"])


class TestVoiceController(unittest.TestCase):
    def test_available_delegates_to_speech_recognizer(self):
        mock_recognizer = MagicMock()
        mock_recognizer.available.return_value = {"success": True, "action": "available"}

        controller = VoiceController(recognizer=mock_recognizer)

        result = controller.available()

        mock_recognizer.available.assert_called_once()
        self.assertTrue(result["success"])

    def test_listen_command_delegates_and_returns_text(self):
        mock_recognizer = MagicMock()
        mock_recognizer.available.return_value = {"success": True, "action": "available"}
        mock_recognizer.listen.return_value = {"success": True, "action": "listen"}
        mock_recognizer.recognize.return_value = {"success": True, "action": "recognize", "result": {"text": "open chrome"}}

        controller = VoiceController(recognizer=mock_recognizer)
        result = controller.listen_command()

        mock_recognizer.available.assert_called_once()
        mock_recognizer.listen.assert_called_once()
        mock_recognizer.recognize.assert_called_once()
        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["text"], "open chrome")

    def test_listen_command_returns_error_when_unavailable(self):
        mock_recognizer = MagicMock()
        mock_recognizer.available.return_value = {"success": False, "action": "available", "message": "Unavailable"}

        controller = VoiceController(recognizer=mock_recognizer)
        result = controller.listen_command()

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Unavailable")


if __name__ == "__main__":
    unittest.main()
