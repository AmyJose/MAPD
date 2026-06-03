from mesa.visualization import (
    CommandConsole,
    Slider,
    SolaraViz,
    SpaceRenderer,
)
from mesa.visualization.components import AgentPortrayalStyle

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
    if agent is None:
        return

    portrayal = AgentPortrayalStyle(
        color="white",
        size=20,
        marker=".",
        zorder=1,
    )

    if isinstance(agent, BlockedCellMarker):
        portrayal.update(
            ("color", "black"),
            ("marker", "s"),
            ("size", 125),
            ("zorder", 1),
        )

    elif isinstance(agent, ParkingMarker):
        portrayal.update(
            ("color", "lightgrey"),
            ("marker", "s"),
            ("size", 30),
            ("zorder", 2),
        )

    elif isinstance(agent, PathMarker):
        portrayal.update(
            ("color", "lightblue"),
            ("marker", "."),
            ("size", 30),
            ("zorder", 3),
        )

    elif isinstance(agent, PickupMarker):
        portrayal.update(
            ("color", "orange"),
            ("marker", "^"),
            ("size", 130),
            ("zorder", 5),
        )

    elif isinstance(agent, DropoffMarker):
        portrayal.update(
            ("color", "red"),
            ("marker", "X"),
            ("size", 130),
            ("zorder", 5),
        )

    elif isinstance(agent, WorkerAgent):
        if getattr(agent, "carrying", False):
            color = "green"
        elif agent.task is not None:
            color = "blue"
        else:
            color = "grey"

        portrayal.update(
            ("color", color),
            ("marker", "o"),
            ("size", 90),
            ("zorder", 10),
        )

    return portrayal


def post_process_space(ax):
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])

    ax.set_title(
        f"MAPD Token Passing — {SCENARIO}",
        fontsize=12,
        pad=10,
    )


model_params = {
    "scenario": {
        "type": "Select",
        "value": SCENARIO,
        "values": ["random", "standard", "test", "warehouse"],
        "label": "Scenario",
    },
    "seed": {
        "type": "InputText",
        "value": SEED,
        "label": "Random seed",
    },
    "task_spawn_probability": Slider(
        "Task spawn probability",
        0.2,
        0.0,
        1.0,
        0.05,
    ),
    "max_tasks_waiting": Slider(
        "Max waiting tasks",
        20,
        1,
        50,
        1,
    ),
}


model = SpaceModel(
    scenario=SCENARIO,
    seed=SEED,
    show_display=True,
)

renderer = SpaceRenderer(
    model,
    backend="matplotlib",
)

renderer.post_process = post_process_space
renderer.draw_agents(agent_portrayal)

page = SolaraViz(
    model,
    renderer,
    components=[CommandConsole],
    model_params=model_params,
    name=f"MAPD Toy Model ({SCENARIO})",
)

page