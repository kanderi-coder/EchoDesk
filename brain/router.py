from knowledge.intent import IntentDetector


class Router:

    def __init__(self):

        self.detector = IntentDetector()

    def route(self, command):

        return self.detector.detect(command)