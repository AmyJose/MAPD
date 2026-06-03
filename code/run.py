from model import SpaceModel
from pathlib import Path
from datetime import datetime
import logging
import argparse


class IgnoreMesaRegistrationLogs(logging.Filter):
    def filter(self, record):
        message = record.getMessage().lower()
        return "registered" not in message and "deregistered" not in message


parser = argparse.ArgumentParser(description="Run the MAPD toy model")

parser.add_argument(
    "--scenario",
    choices=["random", "standard", "test", "warehouse"],
    default="random",
)

parser.add_argument("--seed", type=int, default=None)
parser.add_argument("--steps", type=int, default=500)

# only used for random scenario
parser.add_argument("--width", type=int, default=10)
parser.add_argument("--height", type=int, default=10)
parser.add_argument("--num-workers", type=int, default=3)
parser.add_argument("--num-task-endpoints", type=int, default=8)
parser.add_argument("--blocked-spawn-probability", type=float, default=0.15)
parser.add_argument("--task-spawn-probability", type=float, default=0.2)
parser.add_argument("--max-tasks-waiting", type=int, default=5)

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
    scenario=args.scenario,
    num_workers=args.num_workers,
    num_task_endpoints=args.num_task_endpoints,
    blocked_spawn_probability=args.blocked_spawn_probability,
    task_spawn_probability=args.task_spawn_probability,
    max_tasks_waiting=args.max_tasks_waiting,
    show_display=False,
)

for _ in range(args.steps):
    model.step()

model_data = model.datacollector.get_model_vars_dataframe()
agent_data = model.datacollector.get_agent_vars_dataframe()

worker_data = agent_data[
    agent_data["Agent Type"] == "WorkerAgent"
]

model_data.to_csv(output_dir / "model_data.csv")
worker_data.to_csv(output_dir / "worker_data.csv")

logging.info("Run finished")
logging.info(f"Scenario: {args.scenario}")
logging.info(f"Generated tasks: {model.generated_tasks}")
logging.info(f"Completed tasks: {model.completed_tasks}")
logging.info(f"Vertex collisions: {model.vertex_collisions}")
logging.info(f"Edge collisions: {model.edge_collisions}")

if args.scenario == "test":
    assert model.vertex_collisions == 0, "Vertex collision occurred"
    assert model.edge_collisions == 0, "Edge collision occurred"

print(f"Run successful! Output file location: {output_dir}")