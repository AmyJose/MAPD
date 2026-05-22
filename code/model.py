import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import mesa
from mesa.discrete_space import OrthogonalVonNeumannGrid
from agent import WorkerAgent
from dataclasses import dataclass

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

        self.blocked_cells = {
            self.grid[(3, 3)],
            self.grid[(3,4)],
            self.grid[(3, 5)],
        }

        self.task_spawn_probability = 0.2
        self.max_tasks_waiting = 5
        self.task_endpoints = [
            self.grid[(2, 2)],
            self.grid[(8, 8)],
            self.grid[(1, 7)],
            self.grid[(6, 1)],
            self.grid[(7, 2)],
            self.grid[(4, 8)],
            self.grid[(8, 1)],
            self.grid[(2, 6)],
        ]

        self.tasks = []

        self.workers = []

        start_positions = [
            (0, 0),
            (0, 1),
            (1, 0),
        ]

        for pos in start_positions:
            worker = WorkerAgent(self)
            worker.move_to(self.grid[pos])

            self.workers.append(worker)

    def step(self):
        """Advance by one step"""
        self.maybe_generate_task()

        for worker in self.workers:
            if worker.task is None:
                self.assign_next_task(worker)

        self.agents.shuffle_do("step")
        self.print_grid()

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
            f"dropodd {dropoff.coordinate}"
        )

    def is_done(self):
        return(
            not self.tasks
            and all(worker.task is None for worker in self.workers)
        )
