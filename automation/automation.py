import os
import re
import subprocess
import time
import webbrowser
from typing import Any

try:
    import ctypes
except ImportError:
    ctypes = None


class AutomationEngine:
    """A reusable automation engine for executing desktop actions.

    AutomationEngine provides a unified interface for simple desktop
    automation tasks such as opening applications and websites, typing text,
    sending key presses and hotkeys, moving and clicking the mouse, scrolling,
    and waiting.
    """

    VALID_BUTTONS = {"left", "right", "middle"}
    VALID_SPECIAL_KEYS = {
        "backspace": 0x08,
        "tab": 0x09,
        "enter": 0x0D,
        "shift": 0x10,
        "ctrl": 0x11,
        "control": 0x11,
        "alt": 0x12,
        "pause": 0x13,
        "capslock": 0x14,
        "escape": 0x1B,
        "space": 0x20,
        "pageup": 0x21,
        "pagedown": 0x22,
        "end": 0x23,
        "home": 0x24,
        "left": 0x25,
        "up": 0x26,
        "right": 0x27,
        "down": 0x28,
        "insert": 0x2D,
        "delete": 0x2E,
        "f1": 0x70,
        "f2": 0x71,
        "f3": 0x72,
        "f4": 0x73,
        "f5": 0x74,
        "f6": 0x75,
        "f7": 0x76,
        "f8": 0x77,
        "f9": 0x78,
        "f10": 0x79,
        "f11": 0x7A,
        "f12": 0x7B,
    }

    def __init__(self) -> None:
        """Initialize the automation engine."""
        self._supported = bool(ctypes)

    def process_command(self, command: str) -> dict[str, Any] | None:
        """Parse and execute an automation command.

        Args:
            command: The raw user command.

        Returns:
            A structured result dictionary when the command is recognized, or
            None when the command is not an automation instruction.
        """
        if not isinstance(command, str):
            return None

        raw = command.lower().strip()
        if not raw:
            return None

        patterns = [
            (
                r"^(?:open|visit|go to|navigate to)\s+(?:website\s+)?(?P<url>https?://\S+|www\.\S+|\S+\.\S+)$",
                self.open_website,
            ),
            (r"^(?:wait|sleep|pause)\s+(?P<seconds>\d+(?:\.\d+)?)\s*(?:seconds?)?$", self.wait),
            (
                r"^(?:move mouse to|move the mouse to|move mouse)\s+(?P<x>-?\d+)\s*(?:,|and| )\s*(?P<y>-?\d+)$",
                self.move_mouse,
            ),
            (
                r"^(?:click|double click|right click|middle click)(?:\s+(?P<button>left|right|middle))?(?:\s+at\s+(?P<x>-?\d+)\s*(?:,|and)\s*(?P<y>-?\d+))?$",
                self.click_mouse,
            ),
            (r"^scroll\s+(?P<amount>-?\d+)\s*(?:lines?)?$", self.scroll),
            (r"^(?:press|hit|tap)\s+(?:the\s+)?(?P<key>.+)$", self.press_key),
            (
                r"^(?:press|hit|tap)\s+(?P<keys>(?:ctrl|alt|shift|control)(?:\+|\s+)(?:\w+)(?:\s*(?:\+|\s+)\w+)*)$",
                self.hotkey,
            ),
            (r"^(?:type|enter)\s+(?P<text>.+)$", self.type_text),
            (r"^(?:open|launch|start)\s+(?:application\s+)?(?P<path>.+)$", self.open_application),
        ]

        for pattern, handler in patterns:
            match = re.match(pattern, raw)
            if match:
                return handler(**match.groupdict())

        return None

    def is_automation_command(self, command: str) -> bool:
        """Determine whether a command should be handled by automation."""
        if not isinstance(command, str):
            return False

        return self.process_command(command) is not None

    def open_application(self, path: str) -> dict[str, Any]:
        """Open an application or file.

        Args:
            path: The path or application name to open.

        Returns:
            A structured execution result.
        """
        normalized = path.strip()
        if not normalized:
            return self._error("No application path was provided.")

        try:
            if os.name == "nt":
                if os.path.exists(normalized):
                    os.startfile(normalized)
                else:
                    subprocess.Popen(normalized, shell=True)
            else:
                subprocess.Popen(normalized, shell=True)
        except OSError as exc:
            return self._error("Failed to open the application.", details=str(exc))

        return self._success("open_application", f"Opened application or command: {normalized}.")

    def open_website(self, url: str) -> dict[str, Any]:
        """Open a website in the default web browser.

        Args:
            url: The URL or hostname to open.

        Returns:
            A structured execution result.
        """
        normalized = url.strip()
        if not normalized:
            return self._error("No website URL was provided.")

        if not normalized.startswith(("http://", "https://")):
            normalized = f"https://{normalized}"

        if not self._validate_url(normalized):
            return self._error("The website URL is invalid.")

        try:
            opened = webbrowser.open(normalized)
            if not opened:
                raise RuntimeError("Browser did not open the URL.")
        except Exception as exc:
            return self._error("Failed to open the website.", details=str(exc))

        return self._success("open_website", f"Opened website: {normalized}.")

    def type_text(self, text: str) -> dict[str, Any]:
        """Type text on the keyboard.

        Args:
            text: The text to type.

        Returns:
            A structured execution result.
        """
        normalized = text.strip()
        if not normalized:
            return self._error("No text was provided to type.")

        if not self._supported:
            return self._error("Keyboard automation is not supported in this environment.")

        for char in normalized:
            if not self._send_unicode_char(char):
                return self._error("Unable to type the requested text.")
            time.sleep(0.01)

        return self._success("type_text", f"Typed text: {normalized}.")

    def press_key(self, key: str) -> dict[str, Any]:
        """Press a single keyboard key.

        Args:
            key: The key name.

        Returns:
            A structured execution result.
        """
        normalized = key.strip().lower()
        if not normalized:
            return self._error("No key was specified.")

        vk = self._resolve_key(normalized)
        if vk is None:
            return self._error(f"The key '{key}' is not supported.")

        if not self._supported:
            return self._error("Keyboard automation is not supported in this environment.")

        self._key_down(vk)
        self._key_up(vk)
        return self._success("press_key", f"Pressed key: {normalized}.")

    def hotkey(self, keys: str) -> dict[str, Any]:
        """Press a combination of keys as a hotkey.

        Args:
            keys: A key combination, such as "ctrl+c".

        Returns:
            A structured execution result.
        """
        combination = re.split(r"[+\s]+", keys.strip())
        if len(combination) < 2:
            return self._error("A hotkey requires at least two keys.")

        vk_codes = [self._resolve_key(key.lower()) for key in combination]
        if any(vk is None for vk in vk_codes):
            return self._error(f"The hotkey '{keys}' contains unsupported keys.")

        if not self._supported:
            return self._error("Keyboard automation is not supported in this environment.")

        for vk in vk_codes:
            self._key_down(vk)
            time.sleep(0.02)

        for vk in reversed(vk_codes):
            self._key_up(vk)
            time.sleep(0.02)

        return self._success("hotkey", f"Pressed hotkey: {keys}.")

    def move_mouse(self, x: str, y: str) -> dict[str, Any]:
        """Move the mouse cursor to a specific coordinate.

        Args:
            x: The horizontal pixel coordinate.
            y: The vertical pixel coordinate.

        Returns:
            A structured execution result.
        """
        if not self._validate_coordinate(x) or not self._validate_coordinate(y):
            return self._error("Invalid mouse coordinates.")

        if not self._supported:
            return self._error("Mouse automation is not supported in this environment.")

        try:
            ctypes.windll.user32.SetCursorPos(int(x), int(y))
        except Exception as exc:
            return self._error("Failed to move the mouse.", details=str(exc))

        return self._success("move_mouse", f"Moved mouse to ({x}, {y}).")

    def click_mouse(self, button: str | None = None, x: str | None = None, y: str | None = None) -> dict[str, Any]:
        """Click the mouse at a default or specified location.

        Args:
            button: The mouse button name.
            x: Optional horizontal coordinate.
            y: Optional vertical coordinate.

        Returns:
            A structured execution result.
        """
        button_name = (button or "left").strip().lower()
        if button_name not in self.VALID_BUTTONS:
            return self._error(f"Invalid mouse button: {button_name}.")

        if x is not None and y is not None:
            if not self._validate_coordinate(x) or not self._validate_coordinate(y):
                return self._error("Invalid mouse coordinates.")
            if not self._supported:
                return self._error("Mouse automation is not supported in this environment.")
            ctypes.windll.user32.SetCursorPos(int(x), int(y))

        if not self._supported:
            return self._error("Mouse automation is not supported in this environment.")

        down_flag, up_flag = self._click_flags(button_name)
        try:
            ctypes.windll.user32.mouse_event(down_flag, 0, 0, 0, 0)
            ctypes.windll.user32.mouse_event(up_flag, 0, 0, 0, 0)
        except Exception as exc:
            return self._error("Failed to click the mouse.", details=str(exc))

        description = f"Clicked {button_name} mouse button"
        if x is not None and y is not None:
            description += f" at ({x}, {y})"
        return self._success("click_mouse", f"{description}.")

    def scroll(self, amount: str, x: str | None = None, y: str | None = None) -> dict[str, Any]:
        """Scroll the mouse wheel by a specific amount.

        Args:
            amount: The scroll distance in wheel units.
            x: Optional horizontal coordinate to move before scrolling.
            y: Optional vertical coordinate to move before scrolling.

        Returns:
            A structured execution result.
        """
        if not self._validate_integer(amount):
            return self._error("Invalid scroll amount.")

        if x is not None and y is not None:
            if not self._validate_coordinate(x) or not self._validate_coordinate(y):
                return self._error("Invalid mouse coordinates.")
            if not self._supported:
                return self._error("Mouse automation is not supported in this environment.")
            ctypes.windll.user32.SetCursorPos(int(x), int(y))

        if not self._supported:
            return self._error("Mouse automation is not supported in this environment.")

        try:
            ctypes.windll.user32.mouse_event(0x0800, 0, 0, int(amount) * 120, 0)
        except Exception as exc:
            return self._error("Failed to scroll.", details=str(exc))

        return self._success("scroll", f"Scrolled by {amount} units.")

    def wait(self, seconds: str) -> dict[str, Any]:
        """Pause execution for a specified number of seconds.

        Args:
            seconds: The wait duration.

        Returns:
            A structured execution result.
        """
        if not self._validate_float(seconds):
            return self._error("Invalid wait duration.")

        duration = float(seconds)
        if duration < 0:
            return self._error("Wait duration must be non-negative.")

        time.sleep(duration)
        return self._success("wait", f"Waited for {duration} seconds.")

    def _resolve_key(self, key: str) -> int | None:
        if not key:
            return None

        if key in self.VALID_SPECIAL_KEYS:
            return self.VALID_SPECIAL_KEYS[key]

        if len(key) == 1 and self._supported:
            vk = ctypes.windll.user32.VkKeyScanW(ord(key))
            return vk & 0xFF if vk != -1 else None

        return None

    def _send_unicode_char(self, char: str) -> bool:
        if not self._supported:
            return False

        vk = ctypes.windll.user32.VkKeyScanW(ord(char))
        if vk == -1:
            return False

        vk_code = vk & 0xFF
        shift_state = (vk >> 8) & 0xFF
        if shift_state & 1:
            self._key_down(self.VALID_SPECIAL_KEYS["shift"])
        if shift_state & 2:
            self._key_down(self.VALID_SPECIAL_KEYS["ctrl"])
        if shift_state & 4:
            self._key_down(self.VALID_SPECIAL_KEYS["alt"])

        self._key_down(vk_code)
        self._key_up(vk_code)

        if shift_state & 4:
            self._key_up(self.VALID_SPECIAL_KEYS["alt"])
        if shift_state & 2:
            self._key_up(self.VALID_SPECIAL_KEYS["ctrl"])
        if shift_state & 1:
            self._key_up(self.VALID_SPECIAL_KEYS["shift"])

        return True

    def _key_down(self, vk_code: int) -> None:
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)

    def _key_up(self, vk_code: int) -> None:
        ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)

    def _click_flags(self, button_name: str) -> tuple[int, int]:
        if button_name == "left":
            return 0x0002, 0x0004
        if button_name == "right":
            return 0x0008, 0x0010
        return 0x0020, 0x0040

    def _validate_url(self, url: str) -> bool:
        return bool(re.match(r"^https?://[\w\-]+(\.[\w\-]+)+([/?#].*)?$", url))

    def _validate_coordinate(self, value: str) -> bool:
        return self._validate_integer(value)

    def _validate_integer(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        return bool(re.fullmatch(r"-?\d+", value.strip()))

    def _validate_float(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        return bool(re.fullmatch(r"\d+(?:\.\d+)?", value.strip()))

    def _success(self, action: str, message: str) -> dict[str, Any]:
        return {"success": True, "action": action, "message": message}

    def _error(self, message: str, details: str | None = None) -> dict[str, Any]:
        result = {"success": False, "action": "error", "message": message}
        if details:
            result["details"] = details
        return result
