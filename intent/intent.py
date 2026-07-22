


from typing import Any

from tools.manager import ToolManager


class IntentEngine:

    GREETINGS = (
        "hello",
        "hi",
        "hey",
        "greetings",
        "good morning",
        "good afternoon",
        "good evening",
    )

    QUESTION_WORDS = (
        "who",
        "what",
        "where",
        "when",
        "why",
        "how",
        "which",
    )

    VISION_CUES = (
        "what do you see",
        "look at my screen",
        "read screen",
        "analyze screen",
        "vision",
        "screen",
    )

    INTERNET_CUES = (
        "search",
        "google",
        "wikipedia",
        "browse",
        "internet",
        "web",
        "news",
        "weather",
        "forecast",
        "capital",
        "define",
        "information",
        "info",
        "latest",
        "stock",
        "price",
    )

    MEMORY_CUES = (
        "history",
        "remember",
        "recall",
        "memory",
        "forget",
        "delete",
        "remove",
        "update",
        "change",
    )

    SYSTEM_CUES = (
        "time",
        "screenshot",
        "status",
        "system",
    )

    def classify(self, command):
        if command is None:
            return "unknown"

        text = command.lower().strip()

        if not text:
            return "unknown"

        if self._is_greeting(text):
            return "greeting"

        if self._is_memory(text):
            return "memory"

        if self._is_vision(text):
            return "vision"

        if self._is_internet(text):
            return "internet"

        if self._is_system(text):
            return "system"

        if self._is_question(text):
            return "question"

        return "unknown"

    def _is_greeting(self, text):
        return any(text == phrase or text.startswith(f"{phrase} ") for phrase in self.GREETINGS)

    def _is_question(self, text):
        if text.endswith("?"):
            return True

        first_word = text.split()[0]
        return first_word in self.QUESTION_WORDS

    def _is_system(self, text):
        return any(phrase in text for phrase in self.SYSTEM_CUES)

    def _is_vision(self, text):
        return any(phrase in text for phrase in self.VISION_CUES)

    def _is_internet(self, text):
        return any(phrase in text for phrase in self.INTERNET_CUES)

    def _is_memory(self, text):
        return any(phrase in text for phrase in self.MEMORY_CUES)


class TaskExecutor:

    def __init__(self, intent_engine=None):
        self.intent_engine = intent_engine or IntentEngine()
        self.tool_manager = ToolManager()
        self.tool_manager.register_default_tools()
        self.agent_engine = self.tool_manager.get_tool("AgentEngine")

    def execute(self, command):
        normalized = command.lower().strip() if command else ""

        if command:
            self.tool_manager.execute("ContextEngine", "add_user_message", command)
            if normalized not in ("continue", "history", "time", "screenshot"):
                self.tool_manager.execute("ContextEngine", "set_goal", command)

        if normalized == "history":
            return "history"

        if normalized == "screenshot":
            return "screenshot"

        if normalized == "continue":
            return "knowledge"

        if normalized == "time" or "time" in normalized:
            return "time"

        if self._is_vision_request(normalized):
            return "vision"

        planner_result = self.tool_manager.execute("PlannerEngine", "plan", command)
        if planner_result.get("success") and planner_result.get("result"):
            plan = planner_result["result"]
            self.tool_manager.execute("ContextEngine", "set_goal", command)
            for step in plan.get("steps", []):
                description = step.get("description") or step.get("action")
                self.tool_manager.execute("ContextEngine", "add_pending_task", description)
            self._extract_active_context(plan)
            return "knowledge"

        memory_result = self.tool_manager.execute("MemoryEngine", "is_memory_command", command)
        if memory_result.get("success") and memory_result.get("result"):
            return "knowledge"

        category = self.intent_engine.classify(command)

        if category == "greeting":
            return "greeting"

        if category in ("question", "internet", "memory"):
            return "knowledge"

        if category == "vision":
            return "vision"

        return "unknown"

    def _is_vision_request(self, text):
        return any(phrase in text for phrase in ("what do you see", "look at my screen", "read screen", "analyze screen", "screen"))

    def _extract_active_context(self, plan: dict[str, Any]) -> None:
        if not isinstance(plan, dict):
            return

        for step in plan.get("steps", []):
            action = step.get("action", "").lower()
            target = step.get("target")
            if action == "launch application" and isinstance(target, str):
                self.tool_manager.execute("ContextEngine", "set_active_application", target)
            if action == "open website":
                self.tool_manager.execute("ContextEngine", "set_active_application", "browser")
            if "document" in action or "summarize" in action:
                self.tool_manager.execute("ContextEngine", "set_active_document", target or "document")
