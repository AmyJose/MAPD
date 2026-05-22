from model import SpaceModel

model = SpaceModel(10, 10)

step_count = 0

while not model.is_done():
    print(f"Step {step_count}")
    model.step()
    step_count += 1
    
print(f"Finished in {step_count} steps")