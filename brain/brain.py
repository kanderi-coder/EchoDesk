import datetime
from memory.memory import Memory


class EchoBrain:

    def __init__(self):

        self.name = "EchoDesk"
        self.memory = Memory()


    def process(self, command):

        command = command.lower().strip()


        if "history" in command:

            history = self.memory.recall()

            response = f"I remember {len(history)} conversations."


        elif command in ["hello", "hi", "hey"]:

            response = "Hello! I am EchoDesk. How can I help you?"


        elif "time" in command:

            now = datetime.datetime.now()

            response = f"The current time is {now.strftime('%H:%M:%S')}"


        elif "who are you" in command:

            response = "I am EchoDesk, your personal desktop assistant."


        elif "screenshot" in command:

            response = "Opening my vision system."


        else:

            response = "I am still learning that command."


        self.memory.remember(
            command,
            response
        )


        return response