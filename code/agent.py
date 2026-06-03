import mesa
from mesa.discrete_space import CellAgent
import heapq
from heapq import heappop, heappush
from markers import DropoffMarker, PathMarker, PickupMarker
import logging
logger = logging.getLogger(__name__)

#manhattan distance
def heuristic(a, b):
    ax, ay = a.coordinate
    bx, by = b.coordinate
    return abs(ax-bx) + abs(ay-by)

def a_star(start, goal, other_paths, start_time):
    frontier = []
    heapq.heappush(frontier, (0, 0, start, [start]))

    visited = set()

    while frontier:
        priority, cost, current, path = heappop(frontier)
        current_time = start_time + cost

        if (current, current_time) in visited:
            continue

        visited.add((current, current_time))

        if current == goal:
            return path

        #neighbours = list(current.neighborhood)

        for next_cell in neighbours(current) + [current]:
            next_time = current_time + 1

            if collides_with_token(
                current=current,
                next_cell=next_cell,
                next_time=next_time,
                other_paths=other_paths
            ):
                continue

            new_cost = cost + 1
            heuristic = heuristic(next_cell, goal)
            new_priority = new_cost + heuristic

            heappush(
                frontier,
                (
                    new_priority,
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
        #self.path = []
        #self.carrying = False
        self.worker_id = worker_id
        #self.path_markers = []
        self.token = None
    
    def assign_task(self, task, path=None):
        self.model.token.clear_worker(self)
        self.model.token.clear_endpoint(self)

        if path is None:
            path = a_star(
                start=self.cell,
                goal=task.pickup,
                start_time=self.model.steps,
                worker=self,
                model=self.model
            )   

        #check if a path wasnt found
        if not path and self.cell != task.pickup:
            logger.warning(
                f"Worker {self.worker_id} could not find a path to pickup "
                f"{task.pickup.coordinate}"
            )
            self.task = None
            return False

        self.task = task
        self.carrying = False
        self.path = path
        self.create_path_markers()

        pickup_marker = PickupMarker(self.model)
        pickup_marker.move_to(self.task.pickup)
        self.task.pickup_marker = pickup_marker

        self.model.token.reserve_path(
            worker=self,
            path=self.path,
            start_time=self.model.steps
        )

        logger.debug(
            f"Worker {self.worker_id} planned pickup path: "
            f"{[cell.coordinate for cell in self.path]}"
        )

        return True

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
                h = heuristic(self.cell, task.pickup)
                if h < smallest_h:
                    smallest_h = h
                    t = task

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
            start = self.pos,
            goal = task.pickup,
            other_paths= other_paths,
            start_time=self.model.steps
        )

        if path_to_pickup is None:
            return None
        
        pickup_arrival_time = self.model.steps + len(path_to_pickup) - 1

        #drop off
        path_to_dropoff = a_star(
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
        next_cell = self.model.token.paths[self.worker_id].pop(0)
        self.move_to(next_cell)
    
    def step1(self):
        if self.path:
            current_cell = self.cell
            next_cell = self.path.pop(0)

            occupied_by = [
                worker.worker_id
                for worker in self.model.workers
                if worker is not self and worker.cell == next_cell
            ]

            if occupied_by:
                logger.warning(
                    f"Worker {self.worker_id} blocked from moving "
                    f"{current_cell.coordinate} -> {next_cell.coordinate}; "
                    f"cell occupied by workers {occupied_by}"
                )

                # Put the move back so the worker can try again later
                self.path.insert(0, next_cell)
                logger.debug(
                    f"Worker {self.worker_id} remaining path after block: "
                    f"{[c.coordinate for c in self.path]}"
                )

                # Reserve current cell because the worker is waiting here
                self.model.token.clear_worker(self)
                self.model.token.reserve_path(
                    worker=self,
                    path=self.path,
                    start_time=self.model.steps,
                )

                self.create_path_markers()
                return

            logger.debug(
                f"Worker {self.worker_id} moving "
                f"{current_cell.coordinate} -> {next_cell.coordinate}"
            )

            self.move_to(next_cell)

            assigned_parking = self.model.token.endpoint_assignments.get(self.worker_id)

            if assigned_parking is not None and next_cell != assigned_parking:
                self.model.token.clear_endpoint(self)

            self.create_path_markers()
            return
        
        if self.task is None:
            return
        
        if not self.carrying and self.cell == self.task.pickup:
            logger.info(
                f"Worker {self.worker_id} reached pickup "
                f"{self.task.pickup.coordinate}"
            )

            self.carrying = True

            if self.task.pickup_marker is not None:
                self.task.pickup_marker.remove()
                self.task.pickup_marker = None

            dropoff_marker = DropoffMarker(self.model)
            dropoff_marker.move_to(self.task.dropoff)
            self.task.dropoff_marker = dropoff_marker

            self.model.token.clear_worker(self)

            dropoff_path = a_star(
                start=self.cell, 
                goal=self.task.dropoff, 
                start_time=self.model.steps,
                worker=self,
                model=self.model
            )

            if not dropoff_path and self.cell != self.task.dropoff:
                self.carrying = True
                self.path = []

                logger.warning(
                    f"Worker {self.worker_id} could not find path to dropoff "
                    f"{self.task.dropoff.coordinate}; waiting at pickup "
                    f"{self.cell.coordinate}"
                )

                parked = self.go_to_resting_endpoint()

                if not parked:
                    logger.warning(
                        f"Worker {self.worker_id} could not park; waiting at "
                        f"{self.cell.coordinate}"
                    )

                    self.model.token.reserve_path(
                        worker=self,
                        path=[],
                        start_time=self.model.steps,
                        goal_reserve_horizon=20,
                    )
                return

            self.path=dropoff_path

            self.model.token.reserve_path(
                worker=self,
                path=self.path,
                start_time=self.model.steps
            )

            self.create_path_markers()
            
            logger.debug(
                f"Worker {self.worker_id} planned path: "
                f"{[cell.coordinate for cell in self.path]}"
            )
            return
        
        if self.carrying and self.cell == self.task.dropoff:
            logger.info(
                f"Worker {self.worker_id} completed task at "
                f"{self.task.dropoff.coordinate}"
            )

            self.model.token.clear_worker(self)
            self.clear_path_markers()
            self.model.completed_tasks += 1

            if self.task.dropoff_marker is not None:
                self.task.dropoff_marker.remove()
                self.task.dropoff_marker = None

            self.task = None
            self.carrying = False
            self.path = []

    #helper methods for path markers
    def clear_path_markers(self):
        for marker in self.path_markers:
            marker.remove()

        self.path_markers = []

    def create_path_markers(self):
        self.clear_path_markers()
        for cell in self.path:
            marker = PathMarker(self.model, self.worker_id)
            marker.move_to(cell)
            self.path_markers.append(marker)

    def choose_best_task(self, tasks):
        #use A* to determine the closest pickup location 
        # (what if this was overall location....)
        best_cost = float("inf")
        best_pickup_path = None
        best_task = None
        for task in tasks:
            pickup_path = a_star(
                start=self.cell,
                goal=task.pickup,
                start_time=self.model.steps,
                model=self.model,
                worker=self
            )
            if not pickup_path and self.cell != task.pickup:
                continue

            pickup_arrival_time = self.model.steps + len(pickup_path)

            dropoff_path = a_star(
                start=task.pickup,
                goal=task.dropoff,
                start_time=pickup_arrival_time,
                model=self.model,
                worker=self
            )
            if not dropoff_path and task.pickup != task.dropoff:
                continue

            cost = len(pickup_path) + len(dropoff_path)

            if cost< best_cost:
                best_cost = cost
                best_task = task
                best_pickup_path = pickup_path
        return best_task, best_pickup_path


    def go_to_resting_endpoint(self):
        token = self.model.token

        #if already on a task, get oot
        if self.path:
            return False

        #find the available parking spots
        available_endpoints = [
            cell for cell in self.model.resting_endpoints
            if not token.is_endpoint_taken(cell, self, self.model.workers)
        ]

        if not available_endpoints:
            logger.info(f"Worker {self.worker_id} could not find available parking")
            return False
        
        best_cell = None
        best_path = None
        best_cost = float("inf")

        #short term reserve here?
        # but im not sure that would work as we want it
        for endpoint in available_endpoints:
            path = a_star(
                start=self.cell,
                goal=endpoint,
                start_time=self.model.steps,
                model=self.model,
                worker=self
            )
            if not path and self.cell != endpoint:
                continue

            cost = len(path)

            if cost < best_cost:
                best_cost = cost
                best_cell = endpoint
                best_path = path
        if best_cell is None:
            logger.info(f"Worker {self.worker_id} could not path to parking")
            return False
        
        token.clear_worker(self)
        token.assign_endpoint(self, best_cell)

        self.path = best_path

        #this can be done concurrently. maybe need a short term "looking" reserve.
        token.reserve_path(
            worker=self,
            path=self.path,
            start_time=self.model.steps
        )

        self.create_path_markers()
        logger.info(
            f"Worker {self.worker_id} moving to parking "
            f"{best_cell.coordinate}; path length={len(best_path)}"
        )
        return True


    def request_token(self):
        self.token = self.model.token

    def return_token(self):
        self.token = None
