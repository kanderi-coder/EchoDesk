import os
from typing import Any, Dict, Optional

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    import tkinter
except ImportError:
    tkinter = None

try:
    import win32clipboard
    import win32con
except ImportError:
    win32clipboard = None
    win32con = None


class ClipboardManager:
    """Safely manage clipboard operations across supported Windows environments."""

    def __init__(
        self,
        pyperclip_module: Optional[Any] = None,
        tkinter_module: Optional[Any] = None,
        win32clipboard_module: Optional[Any] = None,
        win32con_module: Optional[Any] = None,
    ) -> None:
        self.pyperclip = pyperclip_module if pyperclip_module is not None else pyperclip
        self.tkinter = tkinter_module if tkinter_module is not None else tkinter
        self.win32clipboard = (
            win32clipboard_module if win32clipboard_module is not None else win32clipboard
        )
        self.win32con = win32con_module if win32con_module is not None else win32con

    def available(self) -> Dict[str, Any]:
        if self._backend_available():
            return self._success("available", "Clipboard functionality is available.")
        return self._error("available", "Clipboard functionality is unavailable.")

    def get_text(self) -> Dict[str, Any]:
        if not self._backend_available():
            return self._error("get_text", "Clipboard is unavailable.")

        try:
            text = self._read_clipboard()
            return self._success("get_text", "Clipboard text retrieved.", result={"text": text})
        except Exception as exc:
            return self._error("get_text", "Failed to read clipboard.", details=str(exc))

    def set_text(self, text: str) -> Dict[str, Any]:
        if not isinstance(text, str):
            return self._error("set_text", "Clipboard text must be a string.")

        if not self._backend_available():
            return self._error("set_text", "Clipboard is unavailable.")

        try:
            self._write_clipboard(text)
            return self._success("set_text", "Clipboard updated.")
        except Exception as exc:
            return self._error("set_text", "Failed to write to clipboard.", details=str(exc))

    def copy(self) -> Dict[str, Any]:
        if not self._backend_available():
            return self._error("copy", "Clipboard is unavailable.")

        try:
            text = self._read_clipboard()
            return self._success("copy", "Clipboard contents copied.", result={"text": text})
        except Exception as exc:
            return self._error("copy", "Failed to copy clipboard contents.", details=str(exc))

    def paste(self) -> Dict[str, Any]:
        if not self._backend_available():
            return self._error("paste", "Clipboard is unavailable.")

        try:
            text = self._read_clipboard()
            return self._success("paste", "Clipboard contents ready.", result={"text": text})
        except Exception as exc:
            return self._error("paste", "Failed to paste clipboard contents.", details=str(exc))

    def clear(self) -> Dict[str, Any]:
        if not self._backend_available():
            return self._error("clear", "Clipboard is unavailable.")

        try:
            self._write_clipboard("")
            return self._success("clear", "Clipboard cleared.")
        except Exception as exc:
            return self._error("clear", "Failed to clear clipboard.", details=str(exc))

    def _backend_available(self) -> bool:
        if self.pyperclip:
            return True
        if self.tkinter and os.name == "nt":
            return True
        if self.win32clipboard and self.win32con:
            return True
        return False

    def _read_clipboard(self) -> str:
        if self.pyperclip:
            return str(self.pyperclip.paste())

        if self.tkinter:
            root = self.tkinter.Tk()
            root.withdraw()
            try:
                value = root.clipboard_get()
                return str(value)
            finally:
                root.destroy()

        if self.win32clipboard and self.win32con:
            self.win32clipboard.OpenClipboard()
            try:
                data = self.win32clipboard.GetClipboardData(self.win32con.CF_UNICODETEXT)
                return str(data)
            finally:
                self.win32clipboard.CloseClipboard()

        raise RuntimeError("No clipboard backend is available.")

    def _write_clipboard(self, text: str) -> None:
        if self.pyperclip:
            self.pyperclip.copy(text)
            return

        if self.tkinter:
            root = self.tkinter.Tk()
            root.withdraw()
            try:
                root.clipboard_clear()
                root.clipboard_append(text)
                root.update()
            finally:
                root.destroy()
            return

        if self.win32clipboard and self.win32con:
            self.win32clipboard.OpenClipboard()
            try:
                self.win32clipboard.EmptyClipboard()
                self.win32clipboard.SetClipboardData(self.win32con.CF_UNICODETEXT, text)
            finally:
                self.win32clipboard.CloseClipboard()
            return

        raise RuntimeError("No clipboard backend is available.")

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
