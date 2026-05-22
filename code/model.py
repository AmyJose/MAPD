import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import mesa
from mesa.discrete_space import OrthogonalVonNeumannGrid
from agent import Agent
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

        self.tasks = [
            Task(self.grid[(2, 2)], self.grid[(8, 8)]),
            Task(self.grid[(1, 7)], self.grid[(6, 1)]),
            Task(self.grid[(7, 2)], self.grid[(4, 8)]),
            Task(self.grid[(8, 1)], self.grid[(2, 6)]),
            Task(self.grid[(5, 1)], self.grid[(9, 9)]),
        ]

        self.workers = []

        start_positions = [
            (0, 0),
            (0, 1),
            (1, 0),
        ]

        for pos in start_positions:
            worker = Agent(self)
            worker.move_to(self.grid[pos])

            self.workers.append(worker)
            self.assign_next_task(worker)

    def step(self):
        """Advance by one step"""
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

    def is_done(self):
        return(
            not self.tasks
            and all(worker.task is None for worker in self.workers)
        )
