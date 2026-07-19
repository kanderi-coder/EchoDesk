class IntentDetector:

    def detect(self, command):

        command = command.lower().strip()

        greetings = [
            "hello",
            "hi",
            "hey"
        ]

        vision = [
            "what do you see",
            "look at my screen",
            "read screen",
            "analyze screen"
        ]

        if command in greetings:
            return "greeting"

        if "time" in command:
            return "time"

        if command == "history":
            return "history"

        if any(x in command for x in vision):
            return "vision"

        if "screenshot" in command:
            return "screenshot"

        if (
            command.startswith("who") or
            command.startswith("what") or
            command.startswith("where") or
            command.startswith("when") or
            command.startswith("why") or
            command.startswith("how")
        ):
            return "knowledge"

        return "unknown"