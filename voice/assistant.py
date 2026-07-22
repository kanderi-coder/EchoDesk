from typing import Any, Dict, Optional

from .speech_recognizer import SpeechRecognizer
from .speech_synthesizer import SpeechSynthesizer

try:
    from brain.brain import EchoBrain
except ImportError:
    EchoBrain = None


class VoiceAssistant:
    """Coordinate speech interaction between microphone, brain, and speech output."""

    def __init__(
        self,
        recognizer: Optional[SpeechRecognizer] = None,
        synthesizer: Optional[SpeechSynthesizer] = None,
        brain: Optional[Any] = None,
    ) -> None:
        self.recognizer = recognizer or SpeechRecognizer()
        self.synthesizer = synthesizer or SpeechSynthesizer()
        self.brain = brain or (EchoBrain() if EchoBrain is not None else None)

    def listen(self) -> Dict[str, Any]:
        available = self.recognizer.available()
        if not available.get("success"):
            return {
                "success": False,
                "stage": "available",
                "message": available.get("message", "Speech recognizer unavailable."),
                "details": available.get("details"),
            }

        listen_result = self.recognizer.listen()
        if not listen_result.get("success"):
            return {
                "success": False,
                "stage": "listen",
                "message": listen_result.get("message", "Failed to listen."),
                "details": listen_result.get("details"),
            }

        return {
            "success": True,
            "stage": "listen",
            "message": "Audio captured.",
        }

    def process_command(self) -> Dict[str, Any]:
        recognize_result = self.recognizer.recognize()
        if not recognize_result.get("success"):
            return {
                "success": False,
                "stage": "recognize",
                "message": recognize_result.get("message", "Failed to recognize speech."),
                "details": recognize_result.get("details"),
            }

        command = recognize_result.get("result", {}).get("text", "")
        if not command:
            return {
                "success": False,
                "stage": "recognize",
                "message": "No command text was recognized.",
            }

        if self.brain is None:
            return {
                "success": False,
                "stage": "process",
                "message": "EchoBrain is unavailable.",
            }

        try:
            response = self.brain.process(command)
            return {
                "success": True,
                "stage": "process",
                "message": "Command processed.",
                "command": command,
                "response": response,
            }
        except Exception as exc:
            return {
                "success": False,
                "stage": "process",
                "message": "Failed to process command.",
                "details": str(exc),
            }

    def respond(self, response: str) -> Dict[str, Any]:
        if not isinstance(response, str) or not response.strip():
            return {
                "success": False,
                "stage": "respond",
                "message": "No text provided for speech output.",
            }

        speak_result = self.synthesizer.speak(response)
        if not speak_result.get("success"):
            return {
                "success": False,
                "stage": "respond",
                "message": speak_result.get("message", "Failed to speak response."),
                "details": speak_result.get("details"),
            }

        return {
            "success": True,
            "stage": "respond",
            "message": "Response spoken.",
            "response": response,
        }

    def run_once(self) -> Dict[str, Any]:
        listen_result = self.listen()
        if not listen_result.get("success"):
            return listen_result

        process_result = self.process_command()
        if not process_result.get("success"):
            return process_result

        respond_result = self.respond(process_result.get("response", ""))
        if not respond_result.get("success"):
            return respond_result

        return {
            "success": True,
            "action": "run_once",
            "command": process_result.get("command"),
            "response": process_result.get("response"),
            "message": "Voice command completed.",
        }
