import ctypes
import datetime
import os
import subprocess
import webbrowser
from typing import Any

try:
    import pyautogui
except ImportError:
    pyautogui = None


class DesktopController:
    """A reusable desktop controller for EchoDesk.

    DesktopController provides modular desktop actions such as moving the mouse,
    clicking buttons, typing text, opening applications and websites, taking
    screenshots, and querying the currently active window.
    """

    VALID_BUTTONS = {"left", "right", "middle"}

    def __init__(self) -> None:
        """Initialize the desktop controller."""
        self.pyautogui = pyautogui
        self.ctypes = ctypes if hasattr(ctypes, "windll") else None

    def move_mouse(self, x: int, y: int) -> dict[str, Any]:
        """Move the mouse cursor to the specified screen coordinates."""
        try:
            x_coord = int(x)
            y_coord = int(y)
        except (TypeError, ValueError):
            return self._error("Invalid mouse coordinates.")

        if self.pyautogui:
            try:
                self.pyautogui.moveTo(x_coord, y_coord)
                return self._success("move_mouse", f"Moved mouse to ({x_coord}, {y_coord}).")
            except Exception as exc:
                return self._error("Failed to move the mouse.", details=str(exc))

        if self.ctypes:
            try:
                self.ctypes.windll.user32.SetCursorPos(x_coord, y_coord)
                return self._success("move_mouse", f"Moved mouse to ({x_coord}, {y_coord}).")
            except Exception as exc:
                return self._error("Failed to move the mouse.", details=str(exc))

        return self._error("Mouse movement is not supported in this environment.")

    def left_click(self) -> dict[str, Any]:
        """Perform a left mouse click."""
        return self._click("left")

    def right_click(self) -> dict[str, Any]:
        """Perform a right mouse click."""
        return self._click("right")

    def middle_click(self) -> dict[str, Any]:
        """Perform a middle mouse click."""
        return self._click("middle")

    def double_click(self) -> dict[str, Any]:
        """Perform a double mouse click."""
        if self.pyautogui:
            try:
                self.pyautogui.doubleClick()
                return self._success("double_click", "Performed a double click.")
            except Exception as exc:
                return self._error("Failed to perform a double click.", details=str(exc))

        if self.ctypes:
            first = self._click("left")
            if not first.get("success"):
                return first
            second = self._click("left")
            if not second.get("success"):
                return second
            return self._success("double_click", "Performed a double click.")

        return self._error("Double click is not supported in this environment.")

    def scroll(self, amount: int) -> dict[str, Any]:
        """Scroll the mouse wheel by a given amount."""
        try:
            scroll_amount = int(amount)
        except (TypeError, ValueError):
            return self._error("Invalid scroll amount.")

        if self.pyautogui:
            try:
                self.pyautogui.scroll(scroll_amount)
                return self._success("scroll", f"Scrolled by {scroll_amount} units.")
            except Exception as exc:
                return self._error("Failed to scroll.", details=str(exc))

        if self.ctypes:
            try:
                self.ctypes.windll.user32.mouse_event(0x0800, 0, 0, scroll_amount * 120, 0)
                return self._success("scroll", f"Scrolled by {scroll_amount} units.")
            except Exception as exc:
                return self._error("Failed to scroll.", details=str(exc))

        return self._error("Scrolling is not supported in this environment.")

    def type_text(self, text: str) -> dict[str, Any]:
        """Type text using the keyboard."""
        if not isinstance(text, str) or not text.strip():
            return self._error("No text was provided to type.")

        if self.pyautogui:
            try:
                self.pyautogui.write(text, interval=0.01)
                return self._success("type_text", f"Typed text: {text}.")
            except Exception as exc:
                return self._error("Failed to type text.", details=str(exc))

        return self._error("Typing text is not supported in this environment.")

    def press_key(self, key: str) -> dict[str, Any]:
        """Press a single keyboard key."""
        if not isinstance(key, str) or not key.strip():
            return self._error("No key was specified.")

        normalized = key.strip().lower()
        if self.pyautogui:
            try:
                self.pyautogui.press(normalized)
                return self._success("press_key", f"Pressed key: {normalized}.")
            except Exception as exc:
                return self._error("Failed to press the key.", details=str(exc))

        return self._error("Key press is not supported in this environment.")

    def hotkey(self, *keys: str) -> dict[str, Any]:
        """Press a key combination as a hotkey."""
        if not keys or not all(isinstance(key, str) and key.strip() for key in keys):
            return self._error("A hotkey requires at least two valid keys.")

        combination = [key.strip().lower() for key in keys]
        if len(combination) < 2:
            return self._error("A hotkey requires at least two keys.")

        if self.pyautogui:
            try:
                self.pyautogui.hotkey(*combination)
                return self._success("hotkey", f"Pressed hotkey: {'+'.join(combination)}.")
            except Exception as exc:
                return self._error("Failed to press the hotkey.", details=str(exc))

        return self._error("Hotkeys are not supported in this environment.")

    def open_application(self, name: str) -> dict[str, Any]:
        """Open an application or command using the desktop environment."""
        if not isinstance(name, str) or not name.strip():
            return self._error("No application name was provided.")

        application = name.strip()

        try:
            if os.name == "nt":
                if os.path.exists(application):
                    os.startfile(application)
                else:
                    subprocess.Popen(application, shell=True)
            else:
                if os.path.exists(application):
                    subprocess.Popen([application])
                else:
                    subprocess.Popen(application, shell=True)
        except Exception as exc:
            return self._error("Failed to open the application.", details=str(exc))

        return self._success("open_application", f"Opened application or command: {application}.")

    def open_website(self, url: str) -> dict[str, Any]:
        """Open a website in the default web browser."""
        if not isinstance(url, str) or not url.strip():
            return self._error("No website URL was provided.")

        normalized = url.strip()
        if not normalized.startswith(("http://", "https://")):
            normalized = f"https://{normalized}"

        try:
            opened = webbrowser.open(normalized)
            if not opened:
                raise RuntimeError("Browser did not open the URL.")
        except Exception as exc:
            return self._error("Failed to open the website.", details=str(exc))

        return self._success("open_website", f"Opened website: {normalized}.")

    def close_application(self, name: str) -> dict[str, Any]:
        """Close an application by name."""
        if not isinstance(name, str) or not name.strip():
            return self._error("No application name was provided.")

        process_name = name.strip()
        try:
            if os.name == "nt":
                completed = subprocess.run(
                    ["taskkill", "/IM", process_name, "/F"],
                    capture_output=True,
                    text=True,
                )
            else:
                completed = subprocess.run(
                    ["pkill", "-f", process_name],
                    capture_output=True,
                    text=True,
                )

            if completed.returncode == 0:
                return self._success("close_application", f"Closed application: {process_name}.")

            return self._error(
                "Failed to close the application.",
                details=completed.stderr.strip() or completed.stdout.strip() or "No matching process found.",
            )
        except Exception as exc:
            return self._error("Failed to close the application.", details=str(exc))

    def take_screenshot(self) -> dict[str, Any]:
        """Take a screenshot and save it to a PNG file."""
        if self.pyautogui:
            try:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                screenshot = self.pyautogui.screenshot()
                screenshot.save(filename)
                return self._success("take_screenshot", f"Screenshot saved to {filename}.", result=filename)
            except Exception as exc:
                return self._error("Failed to take a screenshot.", details=str(exc))

        return self._error("Screenshots are not supported in this environment.")

    def get_active_window(self) -> dict[str, Any]:
        """Return the title of the currently active window."""
        if self.pyautogui:
            window_getter = getattr(self.pyautogui, "getActiveWindow", None)
            if callable(window_getter):
                try:
                    window = window_getter()
                    title = getattr(window, "title", None)
                    if title:
                        return self._success("get_active_window", "Active window retrieved.", result=title)
                except Exception:
                    pass

        if self.ctypes and os.name == "nt":
            try:
                hwnd = self.ctypes.windll.user32.GetForegroundWindow()
                length = self.ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                buffer = self.ctypes.create_unicode_buffer(length + 1)
                self.ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length + 1)
                title = buffer.value
                if title:
                    return self._success("get_active_window", "Active window retrieved.", result=title)
            except Exception as exc:
                return self._error("Failed to get the active window.", details=str(exc))

        return self._error("Unable to determine the active window.")

    def _click(self, button: str) -> dict[str, Any]:
        if button not in self.VALID_BUTTONS:
            return self._error(f"Invalid mouse button: {button}.")

        if self.pyautogui:
            try:
                self.pyautogui.click(button=button)
                return self._success(f"{button}_click", f"Performed a {button} click.")
            except Exception as exc:
                return self._error(f"Failed to perform a {button} click.", details=str(exc))

        if self.ctypes:
            try:
                down_flag, up_flag = self._click_flags(button)
                self.ctypes.windll.user32.mouse_event(down_flag, 0, 0, 0, 0)
                self.ctypes.windll.user32.mouse_event(up_flag, 0, 0, 0, 0)
                return self._success(f"{button}_click", f"Performed a {button} click.")
            except Exception as exc:
                return self._error(f"Failed to perform a {button} click.", details=str(exc))

        return self._error(f"Mouse clicks are not supported in this environment.")

    def _click_flags(self, button_name: str) -> tuple[int, int]:
        if button_name == "left":
            return 0x0002, 0x0004
        if button_name == "right":
            return 0x0008, 0x0010
        return 0x0020, 0x0040

    def _success(self, action: str, message: str, result: Any | None = None) -> dict[str, Any]:
        response = {"success": True, "action": action, "message": message}
        if result is not None:
            response["result"] = result
        return response

    def _error(self, message: str, details: str | None = None) -> dict[str, Any]:
        response = {"success": False, "action": "error", "message": message}
        if details:
            response["details"] = details
        return response
