from model import SpaceModel
from agent import Agent
import mesa

model = SpaceModel(1, 10, 10)

for _ in range(10):
    model.step()