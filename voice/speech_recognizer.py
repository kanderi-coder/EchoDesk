from typing import Any, Dict, Optional

try:
    import speech_recognition as sr
except ImportError:
    sr = None


class SpeechRecognizer:
    """Convert microphone speech to text safely."""

    def __init__(
        self,
        sr_module: Optional[Any] = None,
    ) -> None:
        self.sr = sr_module if sr_module is not None else sr
        self.recognizer = None
        self.audio_data = None

    def initialize(self) -> Dict[str, Any]:
        if not self.sr:
            return self._error("initialize", "Speech recognition library is unavailable.")

        try:
            self.recognizer = self.sr.Recognizer()
            return self._success("initialize", "Speech recognizer initialized.")
        except Exception as exc:
            self.recognizer = None
            return self._error("initialize", "Failed to initialize speech recognizer.", details=str(exc))

    def available(self) -> Dict[str, Any]:
        if not self.sr:
            return self._error("available", "Speech recognition library is unavailable.")

        if not hasattr(self.sr, "Microphone"):
            return self._error("available", "Microphone support is unavailable.")

        try:
            microphone_names = self.sr.Microphone.list_microphone_names()
            if not microphone_names:
                return self._error("available", "No microphone devices were detected.")
            return self._success(
                "available",
                "Microphone and speech recognition are available.",
                result={"device_count": len(microphone_names)},
            )
        except Exception as exc:
            return self._error("available", "Unable to access microphone devices.", details=str(exc))

    def listen(self) -> Dict[str, Any]:
        if not self.sr:
            return self._error("listen", "Speech recognition library is unavailable.")

        if self.recognizer is None:
            init_result = self.initialize()
            if not init_result.get("success"):
                return init_result

        try:
            with self.sr.Microphone() as source:
                audio = self.recognizer.listen(source)
                self.audio_data = audio
                return self._success("listen", "Microphone input captured.")
        except Exception as exc:
            self.audio_data = None
            return self._error("listen", "Failed to capture microphone input.", details=str(exc))

    def recognize(self) -> Dict[str, Any]:
        if not self.sr:
            return self._error("recognize", "Speech recognition library is unavailable.")

        if self.recognizer is None:
            return self._error("recognize", "Speech recognizer is not initialized.")

        if self.audio_data is None:
            return self._error("recognize", "No audio data available. Call listen() first.")

        try:
            text = self.recognizer.recognize_google(self.audio_data)
            return self._success("recognize", "Speech converted to text.", result={"text": text})
        except self.sr.UnknownValueError:
            return self._error("recognize", "Speech was not understood.")
        except self.sr.RequestError as exc:
            return self._error("recognize", "Speech recognition service failed.", details=str(exc))
        except Exception as exc:
            return self._error("recognize", "Failed to recognize speech.", details=str(exc))

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
