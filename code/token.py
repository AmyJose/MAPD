# the shared system token which agents pass around
class Token:
    def __init__(self):
        self.tasks = []
        self.assignments = {}
        self.paths = {}
        self.reserved_cells = {}
        self.reserved_edges = {}

    def add_task(self, task):
        self.tasks.append(task)