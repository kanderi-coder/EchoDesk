from internet.internet import InternetEngine
from automation.automation import AutomationEngine


from memory_engine.memory_engine import MemoryEngine


class KnowledgeEngine:

    def __init__(self):

        self.facts = {

            "who invented python":
                "Python was created by Guido van Rossum and first released in 1991.",

            "what is python":
                "Python is a high-level programming language known for its simplicity and versatility.",

            "what is ai":
                "Artificial Intelligence is the simulation of human intelligence by computers.",

            "what is echodesk":
                "EchoDesk is an AI desktop assistant that can see the screen, understand it, remember conversations and automate tasks.",

            "who are you":
                "I am EchoDesk, your personal desktop AI assistant."
        }

        self.memory_engine = MemoryEngine()
        self.automation_engine = AutomationEngine()
        self.internet_engine = InternetEngine()

    def search(self, question):

        question = question.lower().strip()

        if not question:
            return None

        memory_answer = self.memory_engine.process_command(question)
        if memory_answer is not None:
            return memory_answer

        automation_result = self.automation_engine.process_command(question)
        if automation_result is not None:
            return automation_result.get("message")

        local_answer = self.facts.get(question)
        if local_answer is not None:
            return local_answer

        return self.internet_engine.search(question)