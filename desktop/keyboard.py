import os
import time
from typing import Any, Dict, Optional

try:
    import pyautogui
except ImportError:
    pyautogui = None


class KeyboardController:
    """Safely perform keyboard actions and return structured results."""

    VALID_KEYS = {
        "enter",
        "tab",
        "space",
        "backspace",
        "delete",
        "shift",
        "ctrl",
        "alt",
        "command",
        "cmd",
        "esc",
        "escape",
        "up",
        "down",
        "left",
        "right",
        "home",
        "end",
        "pageup",
        "pagedown",
        "f1",
        "f2",
        "f3",
        "f4",
        "f5",
        "f6",
        "f7",
        "f8",
        "f9",
        "f10",
        "f11",
        "f12",
    }

    def __init__(self, pyautogui_module: Optional[Any] = None) -> None:
        self.pyautogui = pyautogui_module if pyautogui_module is not None else pyautogui

    def type_text(self, text: str) -> Dict[str, Any]:
        if not isinstance(text, str) or not text:
            return self._error("No text was provided to type.")

        if not self.pyautogui:
            return self._error("Keyboard control is unavailable.")

        try:
            self.pyautogui.write(text, interval=0.01)
            return self._success("type_text", "Text entered successfully.")
        except Exception as exc:
            return self._error("Failed to type text.", details=str(exc))

    def press_key(self, key: str) -> Dict[str, Any]:
        if not isinstance(key, str) or not key.strip():
            return self._error("No key was specified.")

        normalized = key.strip().lower()
        if not self._validate_key(normalized):
            return self._error(f"Invalid or unsupported key: {key}.")

        if not self.pyautogui:
            return self._error("Keyboard control is unavailable.")

        try:
            self.pyautogui.press(normalized)
            return self._success("press_key", f"Pressed key: {normalized}.")
        except Exception as exc:
            return self._error("Failed to press the key.", details=str(exc))

    def hotkey(self, *keys: str) -> Dict[str, Any]:
        if not keys or len(keys) < 2:
            return self._error("A hotkey requires at least two keys.")

        normalized_keys = []
        for key in keys:
            if not isinstance(key, str) or not key.strip():
                return self._error("A hotkey requires valid string key names.")
            normalized = key.strip().lower()
            if not self._validate_key(normalized):
                return self._error(f"Invalid or unsupported key in hotkey: {key}.")
            normalized_keys.append(normalized)

        if not self.pyautogui:
            return self._error("Keyboard control is unavailable.")

        try:
            self.pyautogui.hotkey(*normalized_keys)
            return self._success("hotkey", f"Pressed hotkey: {'+'.join(normalized_keys)}.")
        except Exception as exc:
            return self._error("Failed to press the hotkey.", details=str(exc))

    def copy(self) -> Dict[str, Any]:
        return self._modifier_shortcut("c")

    def paste(self) -> Dict[str, Any]:
        return self._modifier_shortcut("v")

    def undo(self) -> Dict[str, Any]:
        return self._modifier_shortcut("z")

    def redo(self) -> Dict[str, Any]:
        return self._modifier_shortcut("y")

    def _modifier_shortcut(self, key: str) -> Dict[str, Any]:
        if not self.pyautogui:
            return self._error("Keyboard control is unavailable.")

        modifier = "ctrl"
        if os.name == "darwin":
            modifier = "command"

        if not self._validate_key(key):
            return self._error(f"Invalid shortcut key: {key}.")

        try:
            self.pyautogui.hotkey(modifier, key)
            return self._success("shortcut", f"Pressed {modifier}+{key}.")
        except Exception as exc:
            return self._error("Failed to execute keyboard shortcut.", details=str(exc))

    def _validate_key(self, key: str) -> bool:
        if not isinstance(key, str) or not key.strip():
            return False

        normalized = key.strip().lower()
        if normalized in self.VALID_KEYS:
            return True
        if len(normalized) == 1 and normalized.isprintable():
            return True
        return False

    def _success(self, action: str, message: str, result: Optional[Any] = None) -> Dict[str, Any]:
        response = {"success": True, "action": action, "message": message}
        if result is not None:
            response["result"] = result
        return response

    def _error(self, message: str, details: Optional[str] = None) -> Dict[str, Any]:
        response = {"success": False, "action": "error", "message": message}
        if details is not None:
            response["details"] = details
        return response
