# the shared system token which agents pass around
class Token:
    def __init__(self):
        self.tasks = []
        self.assignments = {}
        self.paths = {}
        self.reserved_cells = {}
        self.reserved_edges = {}