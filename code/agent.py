import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import mesa
from mesa.discrete_space import CellAgent

class Agent(CellAgent):
    """An agent that can move around a grid"""
    def __init__(self, model, cell):
        super().__init__(model)

        #here is where i will put the agents vars

        self.cell = cell
    
    def move(self):
        self.cell = self.cell.neighborhood.select_random_cell()