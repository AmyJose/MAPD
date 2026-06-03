import solara
import pandas as pd
from mesa.visualization.utils import update_counter
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
            ("color", "gold"),
            ("marker", "^"),
            ("size", 130),
            ("zorder", 5),
        )

    elif isinstance(agent, DropoffMarker):
        portrayal.update(
            ("color", "crimson"),
            ("marker", "X"),
            ("size", 130),
            ("zorder", 5),
        )

    elif isinstance(agent, WorkerAgent):
        if agent.task is None:
            color = "grey"
        elif agent.carrying:
            color = "blue"
        else:
            color = "orange"

        portrayal.update(
            ("color", color),
            ("marker", "o"),
            ("size", 90),
            ("zorder", 10),
        )

    return portrayal


def post_process_space(ax):
    ax.set_aspect("equal")

    ax.set_xticks(range(0, 35, 5))
    ax.set_yticks(range(0, 21, 2))
    ax.grid(True, alpha=0.25)

    ax.set_title(
        f"MAPD Token Passing — {SCENARIO}",
        fontsize=12,
        pad=10,
    )


@solara.component
def WorkerTable(model):
    update_counter.get()

    rows = []

    for worker in model.workers:
        task = worker.task

        rows.append({
            "Worker": worker.worker_id,
            "Position": worker.cell.coordinate if worker.cell else "-",
            "State": (
                "Idle"
                if task is None
                else "Carrying"
                if worker.carrying
                else "To pickup"
            ),
            "Pickup": task.pickup.coordinate if task else "-",
            "Dropoff": task.dropoff.coordinate if task else "-",
        })

    solara.Markdown(f"### Workers — step {model.steps}")
    solara.DataFrame(pd.DataFrame(rows))

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
    components=[
        WorkerTable,
        CommandConsole,
    ],
    model_params=model_params,
    name=f"MAPD Toy Model ({SCENARIO})",
)

page