from dataclasses import dataclass

@dataclass
class ProblemInstance:
    start_cells: list
    task_endpoints: list
    resting_endpoints: list
    blocked_cells: set

    @property
    def endpoints(self):
        return set(self.task_endpoints) | set(self.resting_endpoints)