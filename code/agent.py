import mesa
from mesa.discrete_space import CellAgent
import heapq
from markers import DropoffMarker, PathMarker
import logging
logger = logging.getLogger(__name__)

#manhattan distance
def heuristic(a, b):
    ax, ay = a.coordinate
    bx, by = b.coordinate
    return abs(ax-bx) + abs(ay-by)

#a star function for shortest path finding between two points
# now changed to also care about TIME: what is the shortest route that is free at each timestep
def a_star(start, goal, start_time, model, worker, max_time=100):
    frontier = []
    heapq.heappush(frontier, (0, start.coordinate, start_time, start))

    #dictionarys for lookup
    came_from = {(start, start_time): None}
    current_cost = {(start, start_time): 0}

    while frontier:
        _, _, current_time, current_cell = heapq.heappop(frontier)

        if current_cell == goal:
            break

        if current_time - start_time >= max_time:
            continue

        neighbours = list(current_cell.neighborhood)
        # WAIT action -> adding in the current cell as an option
        neighbours.append(current_cell)

        for next_cell in neighbours:
            next_time = current_time + 1

            if next_cell in model.blocked_cells:
                continue

            if model.token.is_cell_reserved(next_cell, next_time, worker):
                logger.debug(
                    f"Worker {worker.worker_id} rejected "
                    f"{next_cell.coordinate} at t={next_time}; "
                )
                continue

            if model.token.would_swap_edges(current_cell, next_cell, next_time, worker):
                logger.debug(
                    f"Worker {worker.worker_id} rejected edge swap "
                    f"{current_cell.coordinate} -> {next_cell.coordinate} "
                )
                continue

            state = (next_cell, next_time)
            new_cost = current_cost[(current_cell, current_time)] + 1

            if state not in current_cost or new_cost < current_cost[state]:
                current_cost[state] = new_cost

                priority = new_cost +  heuristic(next_cell, goal)

                heapq.heappush(frontier, (priority, next_cell.coordinate, next_time, next_cell))
                came_from[state] = (current_cell, current_time)

    #states where the final entry is one that reaches the goal
    goal_states = [
        state for state in came_from
        if state[0] == goal
    ]

    if not goal_states:
        return []
    
    #which is the best state?
    # the shortest one!
    best_goal_state = min(goal_states, key=lambda state: state[1])
    
    path = []
    current_state = best_goal_state

    while current_state != (start, start_time):
        cell, _ = current_state
        path.append(cell)
        current_state = came_from[current_state]
    
    path.reverse()
    return path


class WorkerAgent(CellAgent):
    """An agent that can move around a grid"""
    def __init__(self, model, worker_id):
        super().__init__(model)
        self.task = None
        self.path = []
        self.carrying = False
        self.worker_id = worker_id
        self.path_markers = []
    
    def assign_task(self, task):
        self.model.token.clear_worker(self)

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
        if self.task is None:
            return
        
        if self.path:
            current_cell = self.cell
            next_cell = self.path.pop(0)

            logger.debug(
                f"Worker {self.worker_id} moving "
                f"{current_cell.coordinate} -> {next_cell.coordinate}"
            )

            self.move_to(next_cell)
            self.create_path_markers()
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

            self.path = a_star(
                start=self.cell, 
                goal=self.task.dropoff, 
                start_time=self.model.steps,
                worker=self,
                model=self.model
            )

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

    def request_token(self):
        token = self.model.token

        if not token.tasks:
            return
        
        task = token.tasks.pop(0)

        success = self.assign_task(task)

        if success:
            #record in token that it is a success
            token.assign_task(self, task)
        else:
            #add it back in
            token.tasks.insert(0, task)
