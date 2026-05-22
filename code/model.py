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

        self.agent = Agent(self)
        self.agent.move_to(self.grid[(0, 0)])

        self.tasks = [
            Task(pickup=self.grid[(2,2)], dropoff=self.grid[(8,8)]),
            Task(pickup=self.grid[(1,7)], dropoff=self.grid[(6,1)]),
            Task(pickup=self.grid[(7,2)], dropoff=self.grid[(4,8)]),
        ]

        self.assign_next_task(self.agent)

    def step(self):
        """Advance by one step"""
        self.agents.shuffle_do("step")
        self.print_grid()

    #code from CHAT GPT to better visualise
    def print_grid(self):
        print()

        for y in reversed(range(self.grid.height)):
            row = ""

            for x in range(self.grid.width):
                cell = self.grid[(x, y)]
                if cell == self.agent.cell:
                    row += "A "
                elif cell in self.blocked_cells:
                    row += "# "
                elif self.agent.task and cell == self.agent.task.pickup:
                    row += "P "
                elif self.agent.task and cell == self.agent.task.dropoff:
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
            and self.agent.task is None
        )
