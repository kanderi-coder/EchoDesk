import ctypes
import time
from typing import Any, Dict, Optional, Tuple

try:
    import pyautogui
except ImportError:
    pyautogui = None


class MouseController:
    """Control mouse actions safely and return structured results."""

    VALID_BUTTONS = {"left", "right", "middle"}
    MAX_COORDINATE = 20000
    MAX_DURATION = 10.0

    def __init__(self, pyautogui_module: Optional[Any] = None, ctypes_module: Optional[Any] = None) -> None:
        self.pyautogui = pyautogui_module if pyautogui_module is not None else pyautogui
        self.ctypes = ctypes_module if ctypes_module is not None else ctypes if hasattr(ctypes, "windll") else None

    def move(self, x: int, y: int) -> Dict[str, Any]:
        if not self._validate_coordinate(x) or not self._validate_coordinate(y):
            return self._error("Invalid mouse coordinates.")

        try:
            if self.pyautogui:
                self.pyautogui.moveTo(int(x), int(y))
                return self._success("move", f"Mouse moved to {x},{y}.")

            if self.ctypes:
                self.ctypes.windll.user32.SetCursorPos(int(x), int(y))
                return self._success("move", f"Mouse moved to {x},{y}.")

            return self._error("Mouse control is unavailable.")
        except Exception as exc:
            return self._error("Failed to move the mouse.", details=str(exc))

    def click(self, button: str = "left") -> Dict[str, Any]:
        normalized = str(button or "").strip().lower()
        if normalized not in self.VALID_BUTTONS:
            return self._error(f"Unsupported mouse button: {button}.")

        try:
            if self.pyautogui:
                self.pyautogui.click(button=normalized)
                return self._success("click", f"Performed a {normalized} click.")

            if self.ctypes:
                return self._click_with_ctypes(normalized)

            return self._error("Mouse control is unavailable.")
        except Exception as exc:
            return self._error("Failed to click the mouse.", details=str(exc))

    def double_click(self, button: str = "left") -> Dict[str, Any]:
        normalized = str(button or "").strip().lower()
        if normalized not in self.VALID_BUTTONS:
            return self._error(f"Unsupported mouse button: {button}.")

        try:
            if self.pyautogui:
                self.pyautogui.doubleClick(button=normalized)
                return self._success("double_click", f"Performed a double {normalized} click.")

            click_one = self.click(normalized)
            if not click_one.get("success"):
                return click_one
            time.sleep(0.05)
            click_two = self.click(normalized)
            if not click_two.get("success"):
                return click_two
            return self._success("double_click", f"Performed a double {normalized} click.")
        except Exception as exc:
            return self._error("Failed to perform a double click.", details=str(exc))

    def drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: float = 1.0,
    ) -> Dict[str, Any]:
        if not all(
            self._validate_coordinate(value)
            for value in (start_x, start_y, end_x, end_y)
        ):
            return self._error("Invalid drag coordinates.")

        if not self._validate_duration(duration):
            return self._error("Invalid drag duration.")

        try:
            if self.pyautogui:
                self.pyautogui.moveTo(int(start_x), int(start_y))
                self.pyautogui.dragTo(int(end_x), int(end_y), duration=min(float(duration), self.MAX_DURATION))
                return self._success(
                    "drag",
                    f"Dragged from {start_x},{start_y} to {end_x},{end_y} in {duration} seconds.",
                )

            if self.ctypes:
                self.move(start_x, start_y)
                self.ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
                time.sleep(min(float(duration), self.MAX_DURATION))
                self.move(end_x, end_y)
                self.ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
                return self._success(
                    "drag",
                    f"Dragged from {start_x},{start_y} to {end_x},{end_y} in {duration} seconds.",
                )

            return self._error("Mouse control is unavailable.")
        except Exception as exc:
            return self._error("Failed to drag the mouse.", details=str(exc))

    def scroll(self, amount: int) -> Dict[str, Any]:
        try:
            scroll_amount = int(amount)
        except (TypeError, ValueError):
            return self._error("Invalid scroll amount.")

        try:
            if self.pyautogui:
                self.pyautogui.scroll(scroll_amount)
                return self._success("scroll", f"Scrolled by {scroll_amount} units.")

            if self.ctypes:
                self.ctypes.windll.user32.mouse_event(0x0800, 0, 0, scroll_amount * 120, 0)
                return self._success("scroll", f"Scrolled by {scroll_amount} units.")

            return self._error("Mouse control is unavailable.")
        except Exception as exc:
            return self._error("Failed to scroll the mouse.", details=str(exc))

    def position(self) -> Dict[str, Any]:
        try:
            if self.pyautogui:
                pos = self.pyautogui.position()
                return self._success("position", "Retrieved mouse position.", result={"x": pos[0], "y": pos[1]})

            if self.ctypes:
                point = self.ctypes.wintypes.POINT()
                if self.ctypes.windll.user32.GetCursorPos(self.ctypes.byref(point)):
                    return self._success(
                        "position",
                        "Retrieved mouse position.",
                        result={"x": point.x, "y": point.y},
                    )
            return self._error("Mouse position retrieval is unavailable.")
        except Exception as exc:
            return self._error("Failed to get mouse position.", details=str(exc))

    def _validate_coordinate(self, value: Any) -> bool:
        try:
            coordinate = int(value)
        except (TypeError, ValueError):
            return False

        if coordinate < 0 or abs(coordinate) > self.MAX_COORDINATE:
            return False

        return True

    def _validate_duration(self, value: Any) -> bool:
        try:
            duration = float(value)
        except (TypeError, ValueError):
            return False

        return 0 <= duration <= self.MAX_DURATION

    def _click_with_ctypes(self, button: str) -> Dict[str, Any]:
        if not self.ctypes:
            return self._error("Mouse control is unavailable.")

        flags = self._click_flags(button)
        if flags is None:
            return self._error(f"Unsupported mouse button: {button}.")

        try:
            self.ctypes.windll.user32.mouse_event(flags[0], 0, 0, 0, 0)
            self.ctypes.windll.user32.mouse_event(flags[1], 0, 0, 0, 0)
            return self._success("click", f"Performed a {button} click.")
        except Exception as exc:
            return self._error("Failed to click the mouse.", details=str(exc))

    def _click_flags(self, button: str) -> Optional[Tuple[int, int]]:
        if button == "left":
            return 0x0002, 0x0004
        if button == "right":
            return 0x0008, 0x0010
        if button == "middle":
            return 0x0020, 0x0040
        return None

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
