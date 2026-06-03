from mesa.visualization import SolaraViz, make_space_component

from model import SpaceModel
from agent import WorkerAgent
from markers import (
    PickupMarker,
    DropoffMarker,
    BlockedCellMarker,
    PathMarker,
    ParkingMarker,
)


SCENARIO = "warehouse"
SEED = 42


def agent_portrayal(agent):
    if isinstance(agent, WorkerAgent):
        if getattr(agent, "carrying", False):
            color = "green"
        elif agent.task is not None:
            color = "blue"
        else:
            color = "grey"

        return {
            "color": color,
            "size": 80,
            "marker": "o",
        }

    if isinstance(agent, PickupMarker):
        return {
            "color": "orange",
            "size": 60,
            "marker": "s",
        }

    if isinstance(agent, DropoffMarker):
        return {
            "color": "red",
            "size": 60,
            "marker": "X",
        }

    if isinstance(agent, BlockedCellMarker):
        return {
            "color": "black",
            "size": 100,
            "marker": "s",
        }

    if isinstance(agent, ParkingMarker):
        return {
            "color": "lightgrey",
            "size": 80,
            "marker": "s",
        }

    if isinstance(agent, PathMarker):
        return {
            "color": "lightblue",
            "size": 25,
            "marker": ".",
        }

    return {
        "color": "white",
        "size": 20,
        "marker": ".",
    }


model = SpaceModel(
    scenario=SCENARIO,
    seed=SEED,
    show_display=True,
)

space_component = make_space_component(agent_portrayal)

page = SolaraViz(
    model,
    components=[space_component],
    name=f"MAPD Toy Model ({SCENARIO})",
)