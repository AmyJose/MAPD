from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

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
        logger.info(
            f"Token added task: "
            f"{task.pickup.coordinate} -> {task.dropoff.coordinate}. "
            f"Waiting tasks={len(self.tasks)}"
        )

    def assign_task(self, worker, task):
        self.assignments[worker.worker_id] = task
        logger.info(
            f"Token assigned task to worker {worker.worker_id}: "
            f"{task.pickup.coordinate} -> {task.dropoff.coordinate}"
        )

    def reserve_path(self, worker, path, start_time):
        worker_id = worker.worker_id
        self.paths[worker_id] = path

        logger.debug(
            f"Token reserving path for worker {worker_id} "
            f"from t={start_time}; path length={len(path)}"
        )

        previous_cell = worker.cell

        for i, cell in enumerate(path):
            timestep = start_time + i + 1

            logger.debug(
                f"Token reserved worker {worker_id}: "
                f"cell {cell.coordinate} at t={timestep}, "
                f"edge {previous_cell.coordinate}->{cell.coordinate}"
            )

            self.reserved_cells[(cell, timestep)] = worker_id
            self.reserved_edges[(previous_cell, cell, timestep)] = worker_id
            previous_cell = cell

    def clear_worker(self, worker):
        worker_id = worker.worker_id

        before_cells = len(self.reserved_cells)
        before_edges = len(self.reserved_edges)
        
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
        logger.debug(
            f"Token cleared worker {worker_id}: "
            f"removed {before_cells - len(self.reserved_cells)} cell reservations, "
            f"{before_edges - len(self.reserved_edges)} edge reservations"
        )

    def is_cell_reserved(self, cell, timestep, worker=None):
        reserved_by = self.reserved_cells.get((cell, timestep))
        worker_id = worker.worker_id if worker is not None else None

        blocked = reserved_by is not None and reserved_by != worker_id

        if blocked:
            logger.debug(
                f"Token cell conflict: cell {cell.coordinate} "
                f"at t={timestep} reserved by worker {reserved_by}; "
                f"requested by worker {worker_id}"
            )

        return blocked
        
    def would_swap_edges(self, from_cell, to_cell, timestep, worker=None):
        reserved_by = self.reserved_edges.get((to_cell, from_cell, timestep))
        worker_id = worker.worker_id if worker is not None else None

        blocked = reserved_by is not None and reserved_by != worker_id

        if blocked:
            logger.debug(
                f"Token edge-swap conflict at t={timestep}: "
                f"{from_cell.coordinate}->{to_cell.coordinate} conflicts with "
                f"worker {reserved_by}'s reverse edge"
            )

        return blocked
    
    