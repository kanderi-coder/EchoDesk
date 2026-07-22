from typing import Any, Dict, Optional

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


class SpeechSynthesizer:
    """Safely convert text to speech."""

    def __init__(
        self,
        pyttsx3_module: Optional[Any] = None,
    ) -> None:
        self.pyttsx3 = pyttsx3_module if pyttsx3_module is not None else pyttsx3
        self.engine = None

    def initialize(self) -> Dict[str, Any]:
        if not self.pyttsx3:
            return self._error("initialize", "Speech engine is unavailable.")

        try:
            self.engine = self.pyttsx3.init()
            return self._success("initialize", "Speech synthesizer initialized.")
        except Exception as exc:
            self.engine = None
            return self._error("initialize", "Failed to initialize speech synthesizer.", details=str(exc))

    def available(self) -> Dict[str, Any]:
        if not self.pyttsx3:
            return self._error("available", "Speech engine is unavailable.")

        try:
            if self.engine is None:
                engine = self.pyttsx3.init()
                self.engine = engine
            return self._success("available", "Speech synthesis is available.")
        except Exception as exc:
            return self._error("available", "Speech synthesis is unavailable.", details=str(exc))

    def speak(self, text: str) -> Dict[str, Any]:
        if not isinstance(text, str) or not text.strip():
            return self._error("speak", "No text was provided to speak.")

        if not self.pyttsx3:
            return self._error("speak", "Speech engine is unavailable.")

        if self.engine is None:
            init_result = self.initialize()
            if not init_result.get("success"):
                return init_result

        try:
            self.engine.say(text)
            self.engine.runAndWait()
            return self._success("speak", "Speech completed.")
        except Exception as exc:
            return self._error("speak", "Failed to speak text.", details=str(exc))

    def stop(self) -> Dict[str, Any]:
        if not self.pyttsx3:
            return self._error("stop", "Speech engine is unavailable.")

        if self.engine is None:
            return self._error("stop", "Speech engine is not initialized.")

        try:
            self.engine.stop()
            return self._success("stop", "Speech stopped.")
        except Exception as exc:
            return self._error("stop", "Failed to stop speech.", details=str(exc))

    def _success(self, action: str, message: str, result: Optional[Any] = None) -> Dict[str, Any]:
        response = {"success": True, "action": action, "message": message}
        if result is not None:
            response["result"] = result
        return response

    def _error(self, action: str, message: str, details: Optional[str] = None) -> Dict[str, Any]:
        response = {"success": False, "action": action, "message": message}
        if details is not None:
            response["details"] = details
        return response
