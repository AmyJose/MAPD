import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import mesa
from mesa.discrete_space import OrthogonalVonNeumannGrid
from agent import Agent


class SpaceModel(mesa.Model):
    """a model containing some number of agents that move around a grid"""

    def __init__(self, n, width, height, seed=None):
        super().__init__(seed=seed)
        self.num_agents = n
        self.grid = OrthogonalVonNeumannGrid((width, height), torus=False, random=self.random)

        agents = Agent.create_agents(
            self,
            self.num_agents,
            self.random.choices(self.grid.all_cells.cells, k=self.num_agents)
        )

    def step(self):
        """Advance by one step"""
        self.agents.shuffle_do("move")