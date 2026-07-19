from intent import TaskExecutor


class Router:

    def __init__(self):

        self.executor = TaskExecutor()

    def route(self, command):

        return self.executor.execute(command)