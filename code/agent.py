import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import mesa
from mesa.discrete_space import CellAgent
import heapq
from markers import DropoffMarker

#manhattan distance
def heuristic(a, b):
    ax, ay = a.coordinate
    bx, by = b.coordinate
    return abs(ax-bx) + abs(ay-by)

#a star function for shortest path finding between two points
# now changed to also care about TIME: what is the shortest route that is free at each timestep
def a_star(start, goal, start_time, model, max_time=100):
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

            if model.is_cell_reserved(next_cell, next_time):
                continue

            if model.would_swap_edges(current_cell, next_cell, next_time):
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
    
    def assign_task(self, task):
        self.task = task
        self.carrying = False
        self.path = a_star(start=self.cell, 
                           goal=task.pickup, 
                           start_time=self.model.steps, 
                           model=self.model)

        self.model.reserve_path(
            worker=self,
            path=self.path,
            start_time=self.model.steps
        )

    def step(self):
        if self.task is None:
            return
        
        if self.path:
            next_cell = self.path.pop(0)
            self.move_to(next_cell)
            return
        
        if not self.carrying and self.cell == self.task.pickup:
            self.carrying = True

            if self.task.pickup_marker is not None:
                self.task.pickup_marker.remove()
                self.task.pickup_marker = None

            dropoff_marker = DropoffMarker(self.model)
            dropoff_marker.move_to(self.task.dropoff)
            self.task.dropoff_marker = dropoff_marker

            self.path = a_star(
                start=self.cell, 
                goal=self.task.dropoff, 
                start_time=self.model.steps,
                model=self.model
            )

            self.model.reserve_path(
                worker=self,
                path=self.path,
                start_time=self.model.steps
            )

            return
        
        if self.carrying and self.cell == self.task.dropoff:
            print(
                f"Worker {self.worker_id} completed task"
            )
            self.model.completed_tasks += 1

            if self.task.dropoff_marker is not None:
                self.task.dropoff_marker.remove()
                self.task.dropoff_marker = None

            self.task = None
            self.carrying = False
            self.path = []

            self.model.assign_next_task(self)