from mesa.discrete_space import CellAgent
from heapq import heappop, heappush
import logging
from itertools import count
logger = logging.getLogger(__name__)

#---------------------helper functions for debug-----------------------
def cell_str(cell):
    if cell is None:
        return "None"
    return str(cell.coordinate)


def path_str(path):
    if not path:
        return "[]"
    return " -> ".join(cell_str(cell) for cell in path)


def task_str(task):
    if task is None:
        return "None"
    return f"{cell_str(task.pickup)} -> {cell_str(task.dropoff)}"

#-----------------------------------------------------------------------

#manhattan distance
def heuristic(a, b):
    ax, ay = a.coordinate
    bx, by = b.coordinate
    return abs(ax-bx) + abs(ay-by)

def a_star(model, start, goal, other_paths, start_offset=0):
    if start is None:
        raise ValueError("a_star received start=None")

    if goal is None:
        raise ValueError("a_star received goal=None")
    
    frontier = []
    tie_breaker = count()
    heappush(frontier, (0, next(tie_breaker), 0, start, [start]))

    visited = set()

    while frontier:
        priority, _ , cost, current, path = heappop(frontier)
        #current_time = start_time + cost

        if (current, cost) in visited:
            continue

        visited.add((current, cost))

        if current == goal:
            return path

        for next_cell in neighbours(current) + [current]:
            if next_cell in model.blocked_cells:
                continue

            next_offset = start_offset + cost + 1

            if collides_with_token(
                current=current,
                next_cell=next_cell,
                next_offset=next_offset,
                other_paths=other_paths
            ):
                continue

            new_cost = cost + 1
            h = model.h_value(next_cell, goal)

            if h == float("inf"):
                continue

            new_priority = new_cost + h

            heappush(
                frontier,
                (
                    new_priority,
                    next(tie_breaker),
                    new_cost,
                    next_cell,
                    path + [next_cell],
                )
            )
                
    return None

def collides_with_token(current, next_cell, next_offset, other_paths):
    for other_path in other_paths.values():
        if not other_path:
            continue

        # after an agent reaches the end of its path, treat it as staying there
        other_current = get_position_at_time(other_path, next_offset - 1)
        other_next = get_position_at_time(other_path, next_offset)

        # vertex collision
        if next_cell == other_next:
            return True

        # edge swap collision
        if current == other_next and next_cell == other_current:
            return True

    return False

def get_position_at_time(path, offset):
    if offset < len(path):
        return path[offset]
    
    return path[-1]

def neighbours(cell):
    return list(cell.neighborhood)

class WorkerAgent(CellAgent):
    """An agent that can move around a grid"""
    def __init__(self, model, worker_id):
        super().__init__(model)
        self.task = None
        self.worker_id = worker_id
        self.token = None
    
    def step(self):
        #request the token
        self.request_token()
        logger.debug(
            f"[t={self.model.steps}] Worker {self.worker_id} STEP START "
            f"at {cell_str(self.cell)} | "
            f"task={task_str(self.task)} | "
            f"token_tasks={len(self.token.tasks)} | "
            f"current_token_path={path_str(self.token.paths.get(self.worker_id))}"
        )   

        #choose a task from the task set such that no path of other agents in the token ends in the pickup or delivery location of the task
        # e.g., available task set = tasks w no current paths to pickup or dropoff in token
        available_tasks = []

        endpoints = {
            path[-1]
            for worker_id, path in self.token.paths.items()
            if worker_id != self.worker_id and path
        }

        logger.debug(
            f"[t={self.model.steps}] Worker {self.worker_id} sees occupied endpoints: "
            f"{[cell_str(cell) for cell in endpoints]}"
        )
        
        for task in self.token.tasks:
            task_available = (
                task.pickup not in endpoints
                and task.dropoff not in endpoints
            )

            logger.debug(
                f"[t={self.model.steps}] Worker {self.worker_id} checking task "
                f"{task_str(task)} | available={task_available}"
            )

            if task_available:
                available_tasks.append(task)

        logger.debug(
            f"[t={self.model.steps}] Worker {self.worker_id} available_tasks="
            f"{[task_str(task) for task in available_tasks]}"
        )

        # if available tasks is not empty
        if available_tasks:
            #pick a task with the smallest h- value from current location to pickup location
            smallest_h = float("inf")
            t = None
            for task in available_tasks:
                h = self.model.h_value(self.cell, task.pickup)
                logger.debug(
                    f"[t={self.model.steps}] Worker {self.worker_id} h-value to task "
                    f"{task_str(task)} = {h}"
                )
                if h < smallest_h:
                    smallest_h = h
                    t = task
            
            if t is None or smallest_h == float("inf"):
                logger.debug(
                    f"[t={self.model.steps}] Worker {self.worker_id} found available tasks "
                    f"but none reachable. Calling Path2."
                )
                self.path2(self.token)
            else:
                logger.info(
                    f"[t={self.model.steps}] Worker {self.worker_id} selected task "
                    f"{task_str(t)} with h={smallest_h}"
                )
                # assign this task to the agent
                self.task = t
                # remove the task from the task set
                self.token.remove_task(self.task)
                # call Path 1
                path = self.path1(self.task, self.token)
                if path is None:
                    logger.warning(
                        f"[t={self.model.steps}] Worker {self.worker_id} Path1 FAILED "
                        f"for task {task_str(self.task)}"
                    )
                else:
                    logger.info(
                        f"[t={self.model.steps}] Worker {self.worker_id} Path1 SUCCESS | "
                        f"path_len={len(path)} | path={path_str(path)}"
                    )
        # else if ( there is no task, so cant assign itself to a task in the current timestep)
        else:
            #no task assignment in current step
            no_task_ends_here = all(task.dropoff != self.cell for task in self.token.tasks)
            
            logger.debug(
                f"[t={self.model.steps}] Worker {self.worker_id} has no available task. "
                f"no_task_ends_here={no_task_ends_here}"
            )
            # if the agent is not in the delivery location of a task in the task set
            if no_task_ends_here:
                # update path in token with trivial path where it rests in its current location
                self.token.paths[self.worker_id] = [self.cell]
                logger.debug(
                    f"[t={self.model.steps}] Worker {self.worker_id} using trivial path "
                    f"at {cell_str(self.cell)}"
                )
            #else (to avoid deadlocks)
            else:
                logger.info(
                    f"[t={self.model.steps}] Worker {self.worker_id} is blocking a task "
                    f"dropoff. Calling Path2."
                )
                # call Path 2:
                path = self.path2(self.token)

                if path is None:
                    logger.warning(
                        f"[t={self.model.steps}] Worker {self.worker_id} Path2 FAILED"
                    )
                else:
                    logger.info(
                        f"[t={self.model.steps}] Worker {self.worker_id} Path2 SUCCESS | "
                        f"path_len={len(path)} | path={path_str(path)}"
                    )
        # return token
        logger.debug(
            f"[t={self.model.steps}] Worker {self.worker_id} STEP END | "
            f"new_token_path={path_str(self.token.paths.get(self.worker_id))}"
        )
        self.return_token()

    
    def path1(self, task, token):
        #path 1 : updates its path in the token w cost minimal path that
            # 1. moves from its current location via the pickup location to the delivery location
            # 2. does not collide with the paths of other agents stored in the token
        
        other_paths = {
            worker_id : path
            for worker_id, path in token.paths.items()
            if worker_id != self.worker_id
        }

        #current position -> pickup
        path_to_pickup = a_star(
            model=self.model,
            start = self.cell,
            goal = task.pickup,
            other_paths= other_paths,
        )

        if path_to_pickup is None:
            logger.warning(
                f"[t={self.model.steps}] Worker {self.worker_id} Path1 failed: "
                f"no path to pickup {cell_str(task.pickup)}"
            )
            return None
        
        pickup_arrival_time = len(path_to_pickup) - 1

        #drop off
        path_to_dropoff = a_star(
            model = self.model,
            start=task.pickup,
            goal = task.dropoff,
            other_paths=other_paths,
            start_offset=pickup_arrival_time,
        )

        if path_to_dropoff is None:
            logger.warning(
                f"[t={self.model.steps}] Worker {self.worker_id} Path1 failed: "
                f"no path from pickup {cell_str(task.pickup)} "
                f"to dropoff {cell_str(task.dropoff)}"
            )
            return None
        
        full_path = path_to_pickup + path_to_dropoff[1:]

        #update the token
        token.paths[self.worker_id] = full_path
        return full_path

    def path2(self, token):
        #path 2: update its path in the token with a cost-minimal path that
            # 1. moves from its current location to an endpoint such that the delivery locations of all tasks in task set are different from the chosen endpoint
            #   and no other path of other agents in the token ends in the chosen endpoint
            # 2. does not collide with the paths of other agents stored in the token

        other_paths = {
            worker_id : path
            for worker_id, path in token.paths.items()
            if worker_id != self.worker_id
        }
        task_dropoffs = {
            task.dropoff
            for task in token.tasks
        }
        occupied_endpoints = {
            path[-1]
            for path in other_paths.values()
            if path
        }
        safe_endpoints = [
            endpoint
            for endpoint in self.model.endpoints
            if endpoint not in task_dropoffs
            and endpoint not in occupied_endpoints
        ]

        best_path = None

        logger.debug(
            f"[t={self.model.steps}] Worker {self.worker_id} Path2 safe_endpoints="
            f"{[cell_str(endpoint) for endpoint in safe_endpoints]}"
        )
        for endpoint in safe_endpoints:
            path = a_star(
                model = self.model,
                start=self.cell,
                goal=endpoint,
                other_paths=other_paths,
            )

            if path is None:
                continue

            if best_path is None or len(path) < len(best_path):
                best_path = path
            
        if best_path is None:
            return None

        token.paths[self.worker_id] = best_path
        return best_path

    def move(self):
        path = self.model.token.paths.get(self.worker_id)

        if not path:
            logger.warning(
                f"[t={self.model.steps}] Worker {self.worker_id} has no path to move"
            )
            return

        old_cell = self.cell

        if len(path) > 1:
            path.pop(0)
            next_cell = path[0]
        else:
            next_cell = path[0]

        self.move_to(next_cell)

        logger.debug(
            f"[t={self.model.steps}] Worker {self.worker_id} MOVE "
            f"{cell_str(old_cell)} -> {cell_str(next_cell)} | "
            f"remaining_path={path_str(path)}"
        )

    def request_token(self):
        self.token = self.model.token

    def return_token(self):
        self.token = None

    def has_reached_end_of_token_path(self):
        path = self.model.token.paths.get(self.worker_id)

        if not path:
            return True
        
        return len(path) <= 1
