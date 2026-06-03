from mesa.discrete_space import CellAgent
from heapq import heappop, heappush
import logging
from itertools import count
logger = logging.getLogger(__name__)

#manhattan distance
def heuristic(a, b):
    ax, ay = a.coordinate
    bx, by = b.coordinate
    return abs(ax-bx) + abs(ay-by)

def a_star(model, start, goal, other_paths, start_time):
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
        current_time = start_time + cost

        if (current, current_time) in visited:
            continue

        visited.add((current, current_time))

        if current == goal:
            return path

        for next_cell in neighbours(current) + [current]:
            if next_cell in model.blocked_cells:
                continue

            next_time = current_time + 1

            if collides_with_token(
                current=current,
                next_cell=next_cell,
                next_time=next_time,
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

def collides_with_token(current, next_cell, next_time, other_paths):
    for other_path in other_paths.values():
        if not other_path:
            continue

        # after an agent reaches the end of its path, treat it as staying there
        other_current = get_position_at_time(other_path, next_time - 1)
        other_next = get_position_at_time(other_path, next_time)

        # vertex collision
        if next_cell == other_next:
            return True

        # edge swap collision
        if current == other_next and next_cell == other_current:
            return True

    return False

def get_position_at_time(path, time):
    if time < len(path):
        return path[time]
    
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
        #choose a task from the task set such that no path of other agents in the token ends in the pickup or delivery location of the task
        # e.g., available task set = tasks w no current paths to pickup or dropoff in token
        available_tasks = []
        for task in self.token.tasks:
            endpoints = {
                path[-1]
                for path in self.token.paths.values()
                if path
            }

            if task.pickup not in endpoints and task.dropoff not in endpoints:
                available_tasks.append(task)

        # if available tasks is not empty
        if available_tasks:
            #pick a task with the smallest h- value from current location to pickup location
            smallest_h = float("inf")
            t = None
            for task in available_tasks:
                h = self.model.h_value(self.cell, task.pickup)
                if h < smallest_h:
                    smallest_h = h
                    t = task
            
            if t is None or smallest_h == float("inf"):
                self.path2(self.token)
            else:
                # assign this task to the agent
                self.task = t
                # remove the task from the task set
                self.token.remove_task(self.task)
                # call Path 1
                self.path1(self.task, self.token)
        # else if ( there is no task, so cant assign itself to a task in the current timestep)
        else:
            #no task assignment in current step
            no_task_ends_here = all(task.dropoff != self.cell for task in self.token.tasks)
            # if the agent is not in the delivery location of a task in the task set
            if no_task_ends_here:
                # update path in token with trivial path where it rests in its current location
                self.token.paths[self.worker_id] = [self.cell]
            #else (to avoid deadlocks)
            else:
                # call Path 2:
                self.path2(self.token)
        # return token
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
            start_time=self.model.steps
        )

        if path_to_pickup is None:
            return None
        
        pickup_arrival_time = self.model.steps + len(path_to_pickup) - 1

        #drop off
        path_to_dropoff = a_star(
            model = self.model,
            start=task.pickup,
            goal = task.dropoff,
            other_paths=other_paths,
            start_time=pickup_arrival_time,
        )

        if path_to_dropoff is None:
            return None
        
        full_path = path_to_pickup + path_to_dropoff[1:]

        #update the token
        token.paths[self.worker_id] = full_path

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
        for endpoint in safe_endpoints:
            path = a_star(
                model = self.model,
                start=self.cell,
                goal=endpoint,
                other_paths=other_paths,
                start_time=self.model.steps
            )

            if path is None:
                continue

            if best_path is None or len(path) < len(best_path):
                best_path = path
            
        if best_path is None:
            return None

        token.paths[self.worker_id] = best_path

    def move(self):
        path = self.model.token.paths.get(self.worker_id)

        if not path:
            return

        if len(path) > 1:
            path.pop(0)
            next_cell = path[0]
            self.move_to(next_cell)
        else:
            self.move_to(path[0])

    def request_token(self):
        self.token = self.model.token

    def return_token(self):
        self.token = None
