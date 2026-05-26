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
def a_star(start, goal, blocked_cells = None):
    blocked_cells = blocked_cells or set()

    frontier = []
    heapq.heappush(frontier, (0, start.coordinate, start))

    #dictionarys for lookup
    came_from = {start: None}
    current_cost = {start: 0}

    while frontier:
        _, _, current = heapq.heappop(frontier)

        if current == goal:
            break

        for neighbour in current.neighborhood:
            if neighbour in blocked_cells:
                continue

            new_cost = current_cost[current] + 1

            if neighbour not in current_cost or new_cost < current_cost[neighbour]:
                current_cost[neighbour] = new_cost
                priority = new_cost +  heuristic(neighbour, goal)
                heapq.heappush(frontier, (priority, neighbour.coordinate, neighbour))
                came_from[neighbour] = current

    if goal not in came_from:
        return []
    
    path = []
    current = goal

    while current != start:
        path.append(current)
        current = came_from[current]
    
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
        self.path = a_star(self.cell, task.pickup, self.model.blocked_cells,)

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

            self.path = a_star(self.cell, self.task.dropoff, self.model.blocked_cells)
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