from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

#what a task is:
@dataclass
class Task:
    pickup: object
    dropoff: object
    pickup_marker: object = None
    dropoff_marker: object = None

# the shared system token which agents pass around
class SystemToken:
    def __init__(self):
        self.tasks = []
        self.paths = {}
        
    def add_task(self, task):
        self.tasks.append(task)
        logger.info(
            f"Token added task: "
            f"{task.pickup.coordinate} -> {task.dropoff.coordinate}. "
            f"Waiting tasks={len(self.tasks)}"
        )

    def remove_task(self, task):
        self.tasks.remove(task)
        logger.info(
            f"Token removed task: "
            f"{task.pickup.coordinate} -> {task.dropoff.coordinate}."
        )
