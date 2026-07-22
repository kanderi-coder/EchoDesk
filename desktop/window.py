import ctypes
import os
from typing import Any, Dict, List, Optional

try:
    import pygetwindow
except ImportError:
    pygetwindow = None

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None


class WindowManager:
    """Safely manage application windows on Windows."""

    SW_MINIMIZE = 6
    SW_MAXIMIZE = 3
    SW_RESTORE = 9
    WM_CLOSE = 0x0010

    def __init__(
        self,
        pygetwindow_module: Optional[Any] = None,
        win32gui_module: Optional[Any] = None,
        win32con_module: Optional[Any] = None,
        ctypes_module: Optional[Any] = None,
    ) -> None:
        self.pygetwindow = pygetwindow_module if pygetwindow_module is not None else pygetwindow
        self.win32gui = win32gui_module if win32gui_module is not None else win32gui
        self.win32con = win32con_module if win32con_module is not None else win32con
        self.ctypes = ctypes_module if ctypes_module is not None else ctypes
        self.user32 = (
            getattr(self.ctypes, "windll", None).user32
            if hasattr(self.ctypes, "windll")
            else None
        )

    def active_window(self) -> Dict[str, Any]:
        if not self._is_windows():
            return self._error(
                "active_window",
                "Window management is only supported on Windows.",
            )

        try:
            title = self._get_active_window_title()
            if not title:
                return self._error("active_window", "No active window was detected.")

            return self._success(
                "active_window",
                "Active window retrieved.",
                result={"window": title},
            )
        except Exception as exc:
            return self._error(
                "active_window",
                "Unable to detect the active window.",
                details=str(exc),
            )

    def list_windows(self) -> Dict[str, Any]:
        if not self._is_windows():
            return self._error(
                "list_windows",
                "Window management is only supported on Windows.",
            )

        try:
            titles = self._get_window_titles()
            return self._success(
                "list_windows",
                "Available windows listed.",
                result={"windows": titles},
            )
        except Exception as exc:
            return self._error(
                "list_windows",
                "Unable to list windows.",
                details=str(exc),
            )

    def focus_window(self, title: str) -> Dict[str, Any]:
        return self._manage_window(title, "focus_window")

    def minimize_window(self, title: str) -> Dict[str, Any]:
        return self._manage_window(title, "minimize_window")

    def maximize_window(self, title: str) -> Dict[str, Any]:
        return self._manage_window(title, "maximize_window")

    def restore_window(self, title: str) -> Dict[str, Any]:
        return self._manage_window(title, "restore_window")

    def close_window(self, title: str, confirm: bool = False) -> Dict[str, Any]:
        if not self._is_windows():
            return self._error(
                "close_window",
                "Window management is only supported on Windows.",
            )

        if not confirm:
            return self._error(
                "close_window",
                "Window close requires explicit confirmation.",
                details="Set confirm=True to close the window.",
            )

        target = self._find_window_target(title)
        if not target:
            return self._error("close_window", "Window not found.", details=title)

        try:
            if hasattr(target, "close"):
                target.close()
            else:
                self._post_close_message(target["hwnd"])

            window_title = target["title"] if isinstance(target, dict) else getattr(target, "title", "")
            return self._success(
                "close_window",
                f"Closed window: {window_title}.",
                result={"window": window_title},
            )
        except Exception as exc:
            return self._error(
                "close_window",
                "Failed to close the window.",
                details=str(exc),
            )

    def switch_window(self, title: str) -> Dict[str, Any]:
        result = self.focus_window(title)
        if result.get("success"):
            result["action"] = "switch_window"
            result["message"] = f"Switched to window: {result.get('result', {}).get('window', title)}."
        return result

    def _manage_window(self, title: str, operation: str) -> Dict[str, Any]:
        if not self._is_windows():
            return self._error(
                operation,
                "Window management is only supported on Windows.",
            )

        target = self._find_window_target(title)
        if not target:
            return self._error(operation, "Window not found.", details=title)

        try:
            window_title = target["title"] if isinstance(target, dict) else getattr(target, "title", "")
            if operation == "focus_window":
                self._activate_window(target)
            elif operation == "minimize_window":
                if callable(getattr(target, "minimize", None)):
                    target.minimize()
                else:
                    self._show_window_ctypes(target["hwnd"], self.SW_MINIMIZE)
            elif operation == "maximize_window":
                if callable(getattr(target, "maximize", None)):
                    target.maximize()
                else:
                    self._show_window_ctypes(target["hwnd"], self.SW_MAXIMIZE)
            elif operation == "restore_window":
                if callable(getattr(target, "restore", None)):
                    target.restore()
                else:
                    self._show_window_ctypes(target["hwnd"], self.SW_RESTORE)
            else:
                return self._error(operation, "Unsupported window operation.")

            return self._success(
                operation,
                f"{operation.replace("_window", "").capitalize()}ed window: {window_title}.",
                result={"window": window_title},
            )
        except Exception as exc:
            return self._error(operation, f"Failed to {operation.replace("_window", " ").strip()}.", details=str(exc))

    def _get_active_window_title(self) -> str:
        if self.pygetwindow and hasattr(self.pygetwindow, "getActiveWindow"):
            active = self.pygetwindow.getActiveWindow()
            return getattr(active, "title", "") or ""

        if self.win32gui:
            hwnd = self.win32gui.GetForegroundWindow()
            return self.win32gui.GetWindowText(hwnd) if hwnd else ""

        if self.user32:
            hwnd = self.user32.GetForegroundWindow()
            if not hwnd:
                return ""
            length = self.user32.GetWindowTextLengthW(hwnd)
            buffer = self.ctypes.create_unicode_buffer(length + 1)
            self.user32.GetWindowTextW(hwnd, buffer, length + 1)
            return buffer.value

        return ""

    def _get_window_titles(self) -> List[str]:
        if self.pygetwindow and hasattr(self.pygetwindow, "getAllTitles"):
            return [title for title in self.pygetwindow.getAllTitles() if title]

        if self.win32gui:
            titles = []

            def callback(hwnd, _):
                if self.win32gui.IsWindowVisible(hwnd):
                    title = self.win32gui.GetWindowText(hwnd)
                    if title:
                        titles.append(title)
                return True

            self.win32gui.EnumWindows(callback, None)
            return titles

        if self.user32:
            return [window["title"] for window in self._enumerate_windows_ctypes()]

        return []

    def _find_window_target(self, title: str) -> Optional[Any]:
        normalized = title.strip().lower()
        if not normalized:
            return None

        if self.pygetwindow and hasattr(self.pygetwindow, "getAllWindows"):
            windows = [
                window
                for window in self.pygetwindow.getAllWindows()
                if getattr(window, "title", "")
            ]
            matched = self._match_windows(windows, normalized)
            return matched

        if self.win32gui:
            windows = self._enumerate_windows_ctypes()
            return self._match_windows(windows, normalized)

        if self.user32:
            windows = self._enumerate_windows_ctypes()
            return self._match_windows(windows, normalized)

        return None

    def _enumerate_windows_ctypes(self) -> List[Dict[str, Any]]:
        windows: List[Dict[str, Any]] = []

        if not self.user32:
            return windows

        WNDENUMPROC = self.ctypes.WINFUNCTYPE(
            self.ctypes.c_bool,
            self.ctypes.c_int,
            self.ctypes.c_int,
        )

        def callback(hwnd: int, _: int) -> bool:
            if self.user32.IsWindowVisible(hwnd):
                length = self.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buffer = self.ctypes.create_unicode_buffer(length + 1)
                    self.user32.GetWindowTextW(hwnd, buffer, length + 1)
                    title = buffer.value
                    if title:
                        windows.append({"hwnd": hwnd, "title": title})
            return True

        self.user32.EnumWindows(WNDENUMPROC(callback), 0)
        return windows

    def _match_windows(self, windows: List[Any], normalized: str) -> Optional[Any]:
        exact_matches = []
        partial_matches = []

        for window in windows:
            title = getattr(window, "title", None) if hasattr(window, "title") else window.get("title", "")
            if not title:
                continue
            title_text = title.strip().lower()
            if title_text == normalized:
                exact_matches.append(window)
            elif normalized in title_text:
                partial_matches.append(window)

        if exact_matches:
            return exact_matches[0]
        if partial_matches:
            return partial_matches[0]
        return None

    def _activate_window(self, target: Any) -> None:
        if hasattr(target, "restore"):
            target.restore()
        if hasattr(target, "activate"):
            target.activate()
            return

        if self.user32:
            self._show_window_ctypes(target["hwnd"], self.SW_RESTORE)
            self.user32.SetForegroundWindow(target["hwnd"])

    def _show_window_ctypes(self, hwnd: int, command: int) -> None:
        if self.user32:
            self.user32.ShowWindow(hwnd, command)

    def _post_close_message(self, hwnd: int) -> None:
        if self.user32:
            self.user32.PostMessageW(hwnd, self.WM_CLOSE, 0, 0)

    def _is_windows(self) -> bool:
        return os.name == "nt"

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
