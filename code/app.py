import solara

from mesa.visualization import SolaraViz, make_space_component
from model import SpaceModel


def agent_portrayal(agent):
    if agent.carrying:
        color = "green"
    elif agent.task is not None:
        color = "blue"
    else:
        color = "grey"

    return {
        "color": color,
        "size": 80,
    }


model = SpaceModel(width=10, height=10)

space_component = make_space_component(agent_portrayal)

page = SolaraViz(
    model,
    components=[space_component],
    name="MAPD Toy Model",
)