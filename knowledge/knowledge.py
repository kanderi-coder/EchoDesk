from internet.internet import InternetEngine
from planner.planner import PlannerEngine


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
        self.planner_engine = PlannerEngine()
        self.internet_engine = InternetEngine()

    def search(self, question):

        question = question.lower().strip()

        if not question:
            return None

        memory_answer = self.memory_engine.process_command(question)
        if memory_answer is not None:
            return memory_answer

        plan = self.planner_engine.plan(question)
        if plan is not None:
            return self.planner_engine.describe_plan(plan)

        local_answer = self.facts.get(question)
        if local_answer is not None:
            return local_answer

        return self.internet_engine.search(question)