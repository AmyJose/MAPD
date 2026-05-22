from model import SpaceModel

model = SpaceModel(10, 10)

max_steps = 100

for step_count in range(max_steps):
    print(f"Step {step_count}")
    model.step()

print(f"Finished after {max_steps} steps")