import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import mesa
from mesa.discrete_space import OrthogonalVonNeumannGrid
from agent import WorkerAgent
from dataclasses import dataclass
from markers import PickupMarker, DropoffMarker, BlockedCellMarker

#what a task is:
@dataclass
class Task:
    pickup: tuple[int, int]
    dropoff: tuple [int,int]

class SpaceModel(mesa.Model):
    """a model containing some number of agents that move around a grid"""

    def __init__(self, width = 10, height = 10, seed=None):
        super().__init__(seed=seed)
        self.grid = OrthogonalVonNeumannGrid((width, height), torus=False, random=self.random)

        self.blocked_spawn_probability = 0.15
        self.num_workers = 3
        self.num_task_endpoints = 8
        self.task_spawn_probability = 0.2
        self.max_tasks_waiting = 5

        self.tasks = []

        self.workers = []

        self.start_cells = self.generate_random_cells(self.num_workers)
        for cell in self.start_cells:
            worker = WorkerAgent(self)
            worker.move_to(cell)
            self.workers.append(worker)

        self.task_endpoints = self.generate_random_cells(self.num_task_endpoints, forbidden=set(self.start_cells))

        self.blocked_cells = self.generate_valid_blocked_cells(forbidden = set(self.start_cells) | set(self.task_endpoints))
        for cell in self.blocked_cells:
            block = BlockedCellMarker(self)
            block.move_to(cell)

    def step(self):
        """Advance by one step"""
        self.maybe_generate_task()

        for worker in self.workers:
            if worker.task is None:
                self.assign_next_task(worker)

        self.agents.shuffle_do("step")
        #self.print_grid()

    #code from CHAT GPT to better visualise
    def print_grid(self):
        print()

        active_pickups = {
            worker.task.pickup
            for worker in self.workers
            if worker.task is not None
        }

        active_dropoffs = {
            worker.task.dropoff
            for worker in self.workers
            if worker.task is not None
        }

        for y in reversed(range(self.grid.height)):
            row = ""

            for x in range(self.grid.width):
                cell = self.grid[(x, y)]

                agent_here = any(worker.cell == cell for worker in self.workers)

                if agent_here:
                    row += "A "
                elif cell in self.blocked_cells:
                    row += "# "
                elif cell in active_pickups:
                    row += "P "
                elif cell in active_dropoffs:
                    row += "D "
                else:
                    row += ". "

            print(row)

        print("-" * 20)

    def assign_next_task(self, agent):
        if not self.tasks:
            print("No tasks left!")
            return
        
        next_task = self.tasks.pop(0)
        agent.assign_task(next_task)

        pickup_marker = PickupMarker(self)
        pickup_marker.move_to(next_task.pickup)
        dropoff_marker = DropoffMarker(self)
        dropoff_marker.move_to(next_task.dropoff)

        print(
            f"Assigned task: pickup {next_task.pickup.coordinate}, "
            f"dropoff {next_task.dropoff.coordinate}"
        )

    # task generator
    def maybe_generate_task(self):
        if len(self.tasks) >= self.max_tasks_waiting:
            return

        if self.random.random() > self.task_spawn_probability:
            return
        
        pickup = self.random.choice(self.task_endpoints)
        dropoff = self.random.choice(self.task_endpoints)

        while dropoff == pickup:
            dropoff = self.random.choice(self.task_endpoints)

        task = Task(pickup=pickup, dropoff=dropoff)
        self.tasks.append(task)

        print(
            f"New task generated: pickup {pickup.coordinate},"
            f"dropoff {dropoff.coordinate}"
        )

    def is_done(self):
        return(
            not self.tasks
            and all(worker.task is None for worker in self.workers)
        )
    
    def generate_valid_blocked_cells(self, forbidden=None, max_attempts=100):
        forbidden = forbidden or set()
        for _ in range(max_attempts):
            blocked_cells = self.generate_blocked_cells(forbidden=forbidden)

            if self.is_connected_for_problem(blocked_cells):
                return blocked_cells
        raise RuntimeError(
            "Could not generate a connected obstacle layout. "
            "Try reducing obstacle_probability."
        )

    def generate_blocked_cells(self, forbidden=None):
        forbidden = forbidden or set()

        blocked_cells = set()

        for cell in self.grid.all_cells:
            if cell in forbidden:
                continue
            if self.random.random() < self.blocked_spawn_probability:
                blocked_cells.add(cell)

        return blocked_cells
    
    def generate_random_cells(self, count, forbidden=None):
        forbidden = forbidden or set()

        available_cells = [
            cell for cell in self.grid.all_cells
            if cell not in forbidden
        ]

        if count > len(available_cells):
            raise ValueError("Not enough available cells to sample from")
        
        return self.random.sample(available_cells, count)
    
    #DFS to ensure all tasks are connected
    def get_reachable_cells(self, start_cell, blocked_cells):
        visited = set()
        frontier = [start_cell]

        while frontier:
            current = frontier.pop()

            if current in visited:
                continue

            visited.add(current)

            for neighbour in current.neighborhood:
                if neighbour in blocked_cells:
                    continue

                if neighbour not in visited:
                    frontier.append(neighbour)

        return visited
    
    def is_connected_for_problem(self, blocked_cells):
        important_cells = set(self.start_cells) | set(self.task_endpoints)

        if not important_cells:
            return True
        
        first_cell = next(iter(important_cells))
        reachable_cells = self.get_reachable_cells(first_cell, blocked_cells)

        return important_cells.issubset(reachable_cells)
