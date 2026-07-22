from typing import Any, Dict, Optional

from .assistant import VoiceAssistant
from .speech_recognizer import SpeechRecognizer
from .speech_synthesizer import SpeechSynthesizer


class VoiceController:
    """Coordinate speech recognition and synthesis for EchoDesk."""

    def __init__(
        self,
        recognizer: Optional[SpeechRecognizer] = None,
        synthesizer: Optional[SpeechSynthesizer] = None,
        assistant: Optional[VoiceAssistant] = None,
    ) -> None:
        self.recognizer = recognizer or SpeechRecognizer()
        self.synthesizer = synthesizer or SpeechSynthesizer()
        self.assistant = assistant or VoiceAssistant(
            recognizer=self.recognizer,
            synthesizer=self.synthesizer,
        )

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

    def speech_available(self) -> Dict[str, Any]:
        return self.synthesizer.available()

    def speak_response(self, text: str) -> Dict[str, Any]:
        return self.synthesizer.speak(text)

    def stop_speech(self) -> Dict[str, Any]:
        return self.synthesizer.stop()

    def run_voice_command(self) -> Dict[str, Any]:
        return self.assistant.run_once()
