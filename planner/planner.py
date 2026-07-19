import re
from typing import Any


class PlannerEngine:
    """A reusable planner engine for EchoDesk.

    PlannerEngine converts user requests into ordered execution plans
    represented as structured steps. It does not execute any actions.
    """

    def __init__(self, automation_engine: Any | None = None):
        """Initialize the planner engine.

        Args:
            automation_engine: Optional automation engine instance used for
                validating automation-related plans without executing them.
        """
        self.automation_engine = automation_engine

    def plan(self, command: str) -> list[dict[str, str]] | None:
        """Translate a natural language command into an execution plan.

        Args:
            command: The user request.

        Returns:
            A list of ordered structured steps or None when the command is not
            suitable for planning.
        """
        if not isinstance(command, str):
            return None

        text = command.strip().lower()
        if not text:
            return None

        routines = [
            self._plan_open_app_and_search,
            self._plan_open_application,
            self._plan_open_website,
            self._plan_read_screen,
            self._plan_time_query,
            self._plan_wait,
            self._plan_move_mouse,
            self._plan_click_mouse,
            self._plan_scroll,
            self._plan_hotkey,
            self._plan_press_key,
            self._plan_type_text,
        ]

        for routine in routines:
            plan = routine(text)
            if plan is not None:
                return plan

        return None

    def describe_plan(self, plan: list[dict[str, str]]) -> str:
        """Return a human-readable description of a plan.

        Args:
            plan: The structured execution plan.

        Returns:
            A numbered summary of the plan steps.
        """
        if not plan:
            return "I could not generate a plan for that request."

        lines = []
        for index, step in enumerate(plan, start=1):
            description = step.get("description") or self._format_step(step)
            lines.append(f"{index}. {description}")

        return "\n".join(lines)

    def is_planning_command(self, command: str) -> bool:
        """Determine whether the command is suitable for planning."""
        return self.plan(command) is not None

    def _plan_open_app_and_search(self, text: str) -> list[dict[str, str]] | None:
        match = re.match(
            r"^(?:open|launch|start)\s+(?:application\s+)?(?P<app>.+?)\s+and\s+search\s+(?P<query>.+)$",
            text,
        )
        if not match:
            return None

        app = self._normalize_application(match.group("app"))
        query = match.group("query").strip()

        return [
            self._step("Launch application", app, f"Launch application: {app}"),
            self._step("Wait", "application", "Wait until the application opens."),
            self._step("Focus search bar", "search", "Focus the search bar."),
            self._step("Type text", query, f"Type \"{query}\"."),
            self._step("Press key", "Enter", "Press Enter."),
        ]

    def _plan_open_application(self, text: str) -> list[dict[str, str]] | None:
        match = re.match(r"^(?:open|launch|start)\s+(?:application\s+)?(?P<app>.+)$", text)
        if not match:
            return None

        app = self._normalize_application(match.group("app"))
        return [
            self._step("Launch application", app, f"Launch application: {app}"),
            self._step("Wait", "application", "Wait until the application opens."),
        ]

    def _plan_open_website(self, text: str) -> list[dict[str, str]] | None:
        match = re.match(
            r"^(?:open|visit|go to|navigate to)\s+(?:website\s+)?(?P<url>https?://\S+|www\.\S+|\S+\.\S+)$",
            text,
        )
        if not match:
            return None

        url = match.group("url").strip()
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        return [
            self._step("Open website", url, f"Open website: {url}"),
            self._step("Wait", "browser", "Wait until the browser opens the website."),
        ]

    def _plan_read_screen(self, text: str) -> list[dict[str, str]] | None:
        if text in (
            "read my screen",
            "read screen",
            "what do you see",
            "analyze my screen",
            "analyze screen",
        ):
            return [
                self._step("Capture screen", "screen", "Capture the screen."),
                self._step("Analyze image", "image", "Analyze the captured image."),
                self._step("Return summary", "summary", "Return a concise summary of the screen contents."),
            ]
        return None

    def _plan_time_query(self, text: str) -> list[dict[str, str]] | None:
        if text in (
            "what time is it",
            "what is the time",
            "tell me the time",
            "current time",
            "time",
        ):
            return [
                self._step("Ask system clock", "clock", "Ask the system clock for the current time."),
                self._step("Return time", "time", "Return the formatted current time."),
            ]
        return None

    def _plan_wait(self, text: str) -> list[dict[str, str]] | None:
        match = re.match(r"^(?:wait|sleep|pause)\s+(?P<seconds>\d+(?:\.\d+)?)\s*(?:seconds?)?$", text)
        if not match:
            return None

        value = match.group("seconds")
        return [
            self._step("Wait", value, f"Wait for {value} seconds."),
        ]

    def _plan_move_mouse(self, text: str) -> list[dict[str, str]] | None:
        match = re.match(
            r"^(?:move mouse to|move the mouse to|move mouse)\s+(?P<x>-?\d+)\s*(?:,|and| )\s*(?P<y>-?\d+)$",
            text,
        )
        if not match:
            return None

        return [
            self._step("Move mouse", f"{match.group('x')},{match.group('y')}", f"Move mouse to ({match.group('x')}, {match.group('y')})."),
        ]

    def _plan_click_mouse(self, text: str) -> list[dict[str, str]] | None:
        match = re.match(
            r"^(?:click|double click|right click|middle click)(?:\s+(?P<button>left|right|middle))?(?:\s+at\s+(?P<x>-?\d+)\s*(?:,|and)\s*(?P<y>-?\d+))?$",
            text,
        )
        if not match:
            return None

        button = (match.group("button") or "left").strip()
        target = "" if not match.group("x") else f"{match.group('x')},{match.group('y')}"
        description = f"Click {button} mouse button"
        if target:
            description += f" at ({target.replace(',', ', ')})"
        description += "."

        return [
            self._step("Click mouse", target or button, description),
        ]

    def _plan_scroll(self, text: str) -> list[dict[str, str]] | None:
        match = re.match(r"^scroll\s+(?P<amount>-?\d+)\s*(?:lines?)?$", text)
        if not match:
            return None

        return [
            self._step("Scroll", match.group("amount"), f"Scroll by {match.group('amount')} units."),
        ]

    def _plan_hotkey(self, text: str) -> list[dict[str, str]] | None:
        match = re.match(
            r"^(?:press|hit|tap)\s+(?P<keys>(?:ctrl|alt|shift|control)(?:\+|\s+)(?:\w+)(?:\s*(?:\+|\s+)\w+)*)$",
            text,
        )
        if not match:
            return None

        combination = re.sub(r"\s+", "+", match.group("keys").strip())
        return [
            self._step("Hotkey", combination, f"Press hotkey: {combination}."),
        ]

    def _plan_press_key(self, text: str) -> list[dict[str, str]] | None:
        match = re.match(r"^(?:press|tap)\s+(?:the\s+)?(?P<key>.+)$", text)
        if not match:
            return None

        key = match.group("key").strip()
        return [
            self._step("Press key", key, f"Press key: {key}."),
        ]

    def _plan_type_text(self, text: str) -> list[dict[str, str]] | None:
        match = re.match(r"^(?:type|enter)\s+(?P<text>.+)$", text)
        if not match:
            return None

        payload = match.group("text").strip()
        return [
            self._step("Type text", payload, f"Type \"{payload}\"."),
        ]

    def _normalize_application(self, app: str) -> str:
        normalized = app.strip().lower()
        normalized = re.sub(r"^(?:the\s+)?", "", normalized)
        if normalized.endswith(" browser"):
            normalized = normalized[: -len(" browser")]
        if normalized.startswith("google "):
            normalized = normalized[len("google ") :]

        if normalized in ("chrome", "google chrome"):
            return "Chrome"
        if normalized in ("firefox", "mozilla firefox"):
            return "Firefox"
        if normalized in ("edge", "microsoft edge"):
            return "Microsoft Edge"
        if normalized in ("notepad", "notepad++"):
            return normalized.title()
        return normalized.title()

    def _step(self, action: str, target: str, description: str) -> dict[str, str]:
        return {"action": action, "target": target, "description": description}

    def _format_step(self, step: dict[str, str]) -> str:
        target = step.get("target")
        if target:
            return f"{step.get('action')}: {target}."
        return step.get("action", "Perform action.")
