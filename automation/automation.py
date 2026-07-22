import os
import re
import subprocess
import time
import webbrowser
from typing import Any

from desktop.controller import DesktopController


class AutomationEngine:
    """A reusable automation engine for executing desktop actions.

    AutomationEngine provides a unified interface for simple desktop
    automation tasks such as opening applications and websites, typing text,
    sending key presses and hotkeys, moving and clicking the mouse, scrolling,
    and waiting.
    """

    VALID_BUTTONS = {"left", "right", "middle"}

    def __init__(self) -> None:
        """Initialize the automation engine."""
        self.controller = DesktopController()

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
            (r"^double click(?:\s+at\s+(?P<x>-?\d+)\s*(?:,|and)\s*(?P<y>-?\d+))?$", self.double_click),
            (
                r"^(?:click|right click|middle click)(?:\s+(?P<button>left|right|middle))?(?:\s+at\s+(?P<x>-?\d+)\s*(?:,|and)\s*(?P<y>-?\d+))?$",
                self.click_mouse,
            ),
            (r"^scroll\s+(?P<amount>-?\d+)\s*(?:lines?)?$", self.scroll),
            (
                r"^(?:press|hit|tap)\s+(?P<keys>(?:ctrl|alt|shift|control)(?:\+|\s+)(?:\w+)(?:\s*(?:\+|\s+)\w+)*)$",
                self.hotkey,
            ),
            (r"^(?:press|hit|tap)\s+(?:the\s+)?(?P<key>.+)$", self.press_key),
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
        """Open an application or file."""
        return self.controller.open_application(path)

    def close_application(self, name: str) -> dict[str, Any]:
        """Close an application by name."""
        return self.controller.close_application(name)

    def take_screenshot(self) -> dict[str, Any]:
        """Capture a screenshot and save it to disk."""
        return self.controller.take_screenshot()

    def get_active_window(self) -> dict[str, Any]:
        """Query the title of the active window."""
        return self.controller.get_active_window()

    def open_website(self, url: str) -> dict[str, Any]:
        """Open a website in the default web browser."""
        return self.controller.open_website(url)

    def type_text(self, text: str) -> dict[str, Any]:
        """Type text on the keyboard."""
        return self.controller.type_text(text)

    def press_key(self, key: str) -> dict[str, Any]:
        """Press a single keyboard key."""
        return self.controller.press_key(key)

    def hotkey(self, keys: str) -> dict[str, Any]:
        """Press a hotkey combination."""
        normalized = keys.strip()
        if not normalized:
            return self._error("A hotkey requires at least two keys.")

        combination = re.split(r"[+\s]+", normalized)
        if len(combination) < 2:
            return self._error("A hotkey requires at least two keys.")

        return self.controller.hotkey(*combination)

    def move_mouse(self, x: str, y: str) -> dict[str, Any]:
        """Move the mouse cursor to a specific coordinate."""
        if not self._validate_coordinate(x) or not self._validate_coordinate(y):
            return self._error("Invalid mouse coordinates.")

        return self.controller.move_mouse(int(x), int(y))

    def left_click(self) -> dict[str, Any]:
        """Perform a left mouse click."""
        return self.controller.left_click()

    def right_click(self) -> dict[str, Any]:
        """Perform a right mouse click."""
        return self.controller.right_click()

    def double_click(self, x: str | None = None, y: str | None = None) -> dict[str, Any]:
        """Perform a double mouse click."""
        if x is not None and y is not None:
            if not self._validate_coordinate(x) or not self._validate_coordinate(y):
                return self._error("Invalid mouse coordinates.")
            move_result = self.controller.move_mouse(int(x), int(y))
            if not move_result.get("success"):
                return move_result

        return self.controller.double_click()

    def click_mouse(self, button: str | None = None, x: str | None = None, y: str | None = None) -> dict[str, Any]:
        """Click the mouse at a default or specified location."""
        target_button = (button or "left").strip().lower()
        if target_button not in self.VALID_BUTTONS:
            return self._error(f"Invalid mouse button: {target_button}.")

        if x is not None and y is not None:
            if not self._validate_coordinate(x) or not self._validate_coordinate(y):
                return self._error("Invalid mouse coordinates.")
            move_result = self.controller.move_mouse(int(x), int(y))
            if not move_result.get("success"):
                return move_result

        if target_button == "left":
            return self.controller.left_click()
        if target_button == "right":
            return self.controller.right_click()
        if target_button == "middle":
            return self.controller.middle_click()
        return self._error(f"Mouse button '{target_button}' is not supported.")

    def scroll(self, amount: str, x: str | None = None, y: str | None = None) -> dict[str, Any]:
        """Scroll the mouse wheel by a specific amount."""
        if not self._validate_integer(amount):
            return self._error("Invalid scroll amount.")

        if x is not None and y is not None:
            if not self._validate_coordinate(x) or not self._validate_coordinate(y):
                return self._error("Invalid mouse coordinates.")
            move_result = self.controller.move_mouse(int(x), int(y))
            if not move_result.get("success"):
                return move_result

        return self.controller.scroll(int(amount))

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
