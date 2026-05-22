import solara

from mesa.visualization import SolaraViz, make_space_component
from model import SpaceModel
from agent import WorkerAgent
from markers import PickupMarker, DropoffMarker, BlockedCellMarker


def agent_portrayal(agent):
    if isinstance(agent, WorkerAgent):
        if agent.carrying:
            color = "green"
        elif agent.task is not None:
            color = "blue"
        else:
            color = "grey"

        return {
            "color": color,
            "size": 80,
            "marker":"o"
        }

    if isinstance(agent, PickupMarker):
        return {
            "color": "orange",
            "size": 60,
            "marker":"s"
        }

    if isinstance(agent, DropoffMarker):
        return {
            "color": "red",
            "size": 60,
            "marker":"X"
        }
    
    if isinstance(agent, BlockedCellMarker):
        return {
            "color": "black",
            "size": 100,
            "marker": "s",
        }

model = SpaceModel(width=10, height=10)

space_component = make_space_component(agent_portrayal)

page = SolaraViz(
    model,
    components=[space_component],
    name="MAPD Toy Model",
)