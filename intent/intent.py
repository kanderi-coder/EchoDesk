


from memory_engine.memory_engine import MemoryEngine


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
        self.memory_engine = MemoryEngine()

    def execute(self, command):
        normalized = command.lower().strip() if command else ""

        if normalized == "history":
            return "history"

        if normalized == "screenshot":
            return "screenshot"

        if normalized == "time" or "time" in normalized:
            return "time"

        if self._is_vision_request(normalized):
            return "vision"

        if self.memory_engine.is_memory_command(command):
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
