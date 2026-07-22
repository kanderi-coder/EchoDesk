import time
from typing import Any, Dict, List, Optional


class DesktopWorkflow:
    """Execute validated desktop workflows through DesktopController."""

    SUPPORTED_ACTIONS = {
        "open_application",
        "move_mouse",
        "click_mouse",
        "type_text",
        "press_key",
        "hotkey",
        "focus_window",
        "minimize_window",
        "maximize_window",
        "get_clipboard",
        "set_clipboard",
        "copy_clipboard",
        "paste_clipboard",
        "wait",
    }

    def __init__(self, controller: Optional[Any] = None) -> None:
        self.controller = controller or DesktopController()

    def available_actions(self) -> List[str]:
        return sorted(self.SUPPORTED_ACTIONS)

    def validate_action(self, action: Any) -> Dict[str, Any]:
        if not isinstance(action, dict):
            return self._error("validate_action", "Each workflow action must be a dictionary.")

        name = action.get("action")
        if not isinstance(name, str) or not name.strip():
            return self._error("validate_action", "Action name must be a non-empty string.")

        name = name.strip()
        if name not in self.SUPPORTED_ACTIONS:
            return self._error(
                "validate_action",
                f"Unsupported workflow action: {name}.",
                details=f"Supported actions: {', '.join(sorted(self.SUPPORTED_ACTIONS))}",
            )

        if name == "open_application" and not action.get("name"):
            return self._error("validate_action", "open_application requires a 'name' field.")

        if name == "move_mouse":
            if "x" not in action or "y" not in action:
                return self._error("validate_action", "move_mouse requires 'x' and 'y' fields.")

        if name == "click_mouse" and not action.get("button"):
            action["button"] = "left"

        if name == "type_text" and not action.get("text"):
            return self._error("validate_action", "type_text requires a 'text' field.")

        if name == "press_key" and not action.get("key"):
            return self._error("validate_action", "press_key requires a 'key' field.")

        if name == "hotkey" and not action.get("keys"):
            return self._error("validate_action", "hotkey requires a 'keys' list.")

        if name in {"focus_window", "minimize_window", "maximize_window"} and not action.get("title"):
            return self._error("validate_action", f"{name} requires a 'title' field.")

        if name == "set_clipboard" and "text" not in action:
            return self._error("validate_action", "set_clipboard requires a 'text' field.")

        if name == "wait" and not ("seconds" in action or "duration" in action):
            return self._error("validate_action", "wait requires a 'seconds' or 'duration' field.")

        if name == "hotkey" and action.get("keys") is not None and not isinstance(action["keys"], list):
            return self._error("validate_action", "hotkey keys must be a list of strings.")

        return self._success("validate_action", "Action is valid.")

    def execute(self, actions: Any) -> Dict[str, Any]:
        if not isinstance(actions, list):
            return self._error("execute", "Workflow actions must be provided as a list.")

        completed = 0
        results: List[Dict[str, Any]] = []

        for action in actions:
            validation = self.validate_action(action)
            if not validation.get("success"):
                results.append(validation)
                return {
                    "success": False,
                    "action": "execute",
                    "message": "Workflow validation failed.",
                    "completed": completed,
                    "results": results,
                }

            action_result = self._perform_action(action)
            results.append(action_result)
            if not action_result.get("success"):
                return {
                    "success": False,
                    "action": "execute",
                    "message": "Workflow execution stopped due to failure.",
                    "completed": completed,
                    "results": results,
                }

            completed += 1

        return {
            "success": True,
            "action": "execute",
            "message": "Workflow executed successfully.",
            "completed": completed,
            "results": results,
        }

    def _perform_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        name = action["action"].strip()

        if name == "open_application":
            return self.controller.open_application(action["name"])

        if name == "move_mouse":
            return self.controller.move_mouse(action["x"], action["y"])

        if name == "click_mouse":
            return self.controller.click_mouse(action.get("button", "left"))

        if name == "type_text":
            return self.controller.type_text(action["text"])

        if name == "press_key":
            return self.controller.press_key(action["key"])

        if name == "hotkey":
            keys = action.get("keys", [])
            return self.controller.hotkey(*keys)

        if name == "focus_window":
            return self.controller.focus_window(action["title"])

        if name == "minimize_window":
            return self.controller.minimize_window(action["title"])

        if name == "maximize_window":
            return self.controller.maximize_window(action["title"])

        if name == "get_clipboard":
            return self.controller.get_clipboard()

        if name == "set_clipboard":
            return self.controller.set_clipboard(action["text"])

        if name == "copy_clipboard":
            return self.controller.copy_clipboard()

        if name == "paste_clipboard":
            return self.controller.paste_clipboard()

        if name == "wait":
            seconds = action.get("seconds", action.get("duration", 0))
            try:
                seconds = float(seconds)
            except (TypeError, ValueError):
                return self._error("wait", "Invalid wait duration.")
            time.sleep(max(0.0, seconds))
            return self._success("wait", f"Waited for {seconds} seconds.")

        return self._error("execute", f"Unsupported workflow action: {name}.")

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
