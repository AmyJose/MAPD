from model import SpaceModel

model = SpaceModel(10, 10)

for _ in range(30):
    model.step()