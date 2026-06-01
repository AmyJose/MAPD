from model import SpaceModel
from pathlib import Path
from datetime import datetime
import logging
import argparse

parser = argparse.ArgumentParser(description="Run the MAPD toy model")

parser.add_argument(
    "--scenario",
    choices=["random", "standard"],
    default="random",
    help="Choose whether to run a random world or the fixed standard test world",
)

parser.add_argument(
    "--seed",
    type=int,
    default=None,
    help="Random seed for repeatable runs",
)

parser.add_argument(
    "--steps",
    type=int,
    default=500,
    help="Number of simulation steps to run",
)

args = parser.parse_args()

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = Path("results") / timestamp
output_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=output_dir / "simulation.log",
    filemode="w",
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

model = SpaceModel(
    width=10,
    height=10,
    scenario=args.scenario
)

for step_count in range(args.steps):
    model.step()

model_data = model.datacollector.get_model_vars_dataframe()
agent_data = model.datacollector.get_agent_vars_dataframe()

worker_data = agent_data[
    agent_data["Agent Type"] == "WorkerAgent"
]

model_data.to_csv(output_dir / "model_data.csv")
worker_data.to_csv(output_dir / "worker_data.csv")

logging.info("Run finished")
logging.info(f"Generated tasks: {model.generated_tasks}")
logging.info(f"Completed tasks: {model.completed_tasks}")
logging.info(f"Vertex collisions: {model.vertex_collisions}")
logging.info(f"Edge collisions: {model.edge_collisions}")

print(f"Run successful! Output file location: {output_dir}")