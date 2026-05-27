from model import SpaceModel
from pathlib import Path
from datetime import datetime
import logging

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = Path("results") / timestamp
output_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=output_dir / "simulation.log",
    filemode="w",
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

model = SpaceModel(10, 10)

max_steps = 500

for step_count in range(max_steps):
    model.step()

model_data = model.datacollector.get_model_vars_dataframe()
agent_data = model.datacollector.get_agent_vars_dataframe()

worker_data = agent_data[
    agent_data["Agent Type"] == "WorkerAgent"
]

model_data.to_csv(output_dir / "model_data.csv")
worker_data.to_csv(output_dir / "worker_data.csv")
