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

    def search(self, question):

        question = question.lower().strip()

        return self.facts.get(question, None)