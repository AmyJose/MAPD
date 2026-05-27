from model import SpaceModel
from pathlib import Path
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

model = SpaceModel(10, 10)

max_steps = 100

for step_count in range(max_steps):
    print(f"Step {step_count}:")
    model.step()

print(f"Finished after {max_steps} steps")

model_data = model.datacollector.get_model_vars_dataframe()
agent_data = model.datacollector.get_agent_vars_dataframe()

worker_data = agent_data[
    agent_data["Agent Type"] == "WorkerAgent"
]

output_dir = Path("results") / timestamp
output_dir.mkdir(parents=True, exist_ok=True)

model_data.to_csv(output_dir / "model_data.csv")
worker_data.to_csv(output_dir / "worker_data.csv")

print(f"Generated tasks: {model.generated_tasks}")
print(f"Completed tasks: {model.completed_tasks}")

print(f"Vertex collisions: {model.vertex_collisions}")
print(f"Edge collisions: {model.edge_collisions}")