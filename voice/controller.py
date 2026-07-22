from typing import Any, Dict, Optional

from .speech_recognizer import SpeechRecognizer


class VoiceController:
    """Coordinate speech recognition input for EchoDesk."""

    def __init__(
        self,
        recognizer: Optional[SpeechRecognizer] = None,
    ) -> None:
        self.recognizer = recognizer or SpeechRecognizer()

    def available(self) -> Dict[str, Any]:
        return self.recognizer.available()

    def listen_command(self) -> Dict[str, Any]:
        availability = self.available()
        if not availability.get("success"):
            return availability

        listen_result = self.recognizer.listen()
        if not listen_result.get("success"):
            return listen_result

        recognize_result = self.recognizer.recognize()
        if not recognize_result.get("success"):
            return recognize_result

        return {
            "success": True,
            "action": "listen_command",
            "message": "Speech command received.",
            "result": recognize_result.get("result"),
        }
