from model import SpaceModel
from pathlib import Path
from datetime import datetime
import logging
import argparse

class IgnoreMesaRegistrationLogs(logging.Filter):
    def filter(self, record):
        message = record.getMessage().lower()

        ignored_phrases = [
            "registered",
            "deregistered",
        ]

        return not any(phrase in message for phrase in ignored_phrases)

parser = argparse.ArgumentParser(description="Run the MAPD toy model")

parser.add_argument(
    "--scenario",
    choices=["random", "standard", "test", "warehouse"],
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

parser.add_argument(
    "--width",
    type=int,
    default=10,
    help="Width of grid",
)

parser.add_argument(
    "--height",
    type=int,
    default=10,
    help="Height of grid",
)

args = parser.parse_args()

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = Path("results") / timestamp
output_dir.mkdir(parents=True, exist_ok=True)

log_file = output_dir / "simulation.log"

file_handler = logging.FileHandler(log_file, mode="w")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
)
file_handler.addFilter(IgnoreMesaRegistrationLogs())

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.handlers.clear()
root_logger.addHandler(file_handler)

model = SpaceModel(
    width=args.width,
    height=args.height,
    seed=args.seed,
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

if args.scenario == "test":
    assert model.vertex_collisions == 0, "Vertex Collision occurred"
    assert model.vertex_collisions == 0, "Edge Collision occured"

print(f"Run successful! Output file location: {output_dir}")