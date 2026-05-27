from dataclasses import dataclass

#what a task is:
@dataclass
class Task:
    pickup: tuple[int, int]
    dropoff: tuple [int,int]
    pickup_marker: object = None
    dropoff_marker: object = None

# the shared system token which agents pass around
class SystemToken:
    def __init__(self):
        self.tasks = []
        self.assignments = {}
        self.paths = {}
        self.reserved_cells = {}
        self.reserved_edges = {}

    def add_task(self, task):
        self.tasks.append(task)

    def assign_task(self, worker, task):
        self.assignments[worker.worker_id] = task

    def reserve_path(self, worker, path, start_time):
        worker_id = worker.worker_id
        self.paths[worker_id] = path

        previous_cell = worker.cell

        for i, cell in enumerate(path):
            timestep = start_time + i + 1

            self.reserved_cells[(cell, timestep)] = worker_id
            self.reserved_edges[(previous_cell, cell, timestep)] = worker_id
            previous_cell = cell

    def clear_worker(self, worker):
        worker_id = worker.worker_id
        
        self.assignments.pop(worker_id, None)
        self.paths.pop(worker_id, None)

        self.reserved_cells = {
            key: value
            for key, value in self.reserved_cells.items()
            if value != worker_id
        }

        self.reserved_edges = {
            key: value
            for key, value in self.reserved_edges.items()
            if value != worker_id
        }

    def is_cell_reserved(self, cell, timestep, worker=None):
        reserved_by=self.reserved_cells.get((cell, timestep))
        return reserved_by is not None and reserved_by is not worker
    
    def would_swap_edges(self, from_cell, to_cell, timestep, worker=None):
        reserved_by= self.reserved_edges.get((to_cell, from_cell, timestep))
        return reserved_by is not None and reserved_by is not worker
    
    