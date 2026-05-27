from mesa.discrete_space import CellAgent

class PickupMarker(CellAgent):
    def step(self):
        pass

class DropoffMarker(CellAgent):
    def step(self):
        pass
    
class BlockedCellMarker(CellAgent):
    def step(self):
        pass

class PathMarker(CellAgent):
    def __init__(self, model, worker_id):
        super().__init__(model)
        self.worker_id = worker_id
    def step(self):
        pass