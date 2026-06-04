from markers import (
    RestingEndpointMarker,
    TaskEndpointMarker,
    BlockedCellMarker,
    PathMarker,
    PickupMarker,
    DropoffMarker,
)
import logging

logger = logging.getLogger(__name__)


class DisplayLayer:
    def __init__(self, model):
        self.model = model
        self.static_markers = []
        self.path_markers = []
        self.task_markers = []

    def create_static_markers(self):
        # grey task endpoint squares
        for cell in self.model.task_endpoints:
            marker = TaskEndpointMarker(self.model)
            marker.move_to(cell)
            self.static_markers.append(marker)

        # resting endpoints
        for cell in self.model.resting_endpoints:
            marker = RestingEndpointMarker(self.model)
            marker.move_to(cell)
            self.static_markers.append(marker)

        # blocked shelves
        for cell in self.model.blocked_cells:
            marker = BlockedCellMarker(self.model)
            marker.move_to(cell)
            self.static_markers.append(marker)

    def update(self):
        self.update_task_markers()
        self.update_path_markers()

    def clear_markers(self, markers):
        for marker in markers:
            marker.remove()

        markers.clear()

    def update_task_markers(self):
        self.clear_markers(self.task_markers)

        for worker in self.model.workers:
            task = worker.task

            if task is None:
                continue

            if not worker.carrying:
                pickup_marker = PickupMarker(self.model)
                pickup_marker.move_to(task.pickup)
                self.task_markers.append(pickup_marker)

            dropoff_marker = DropoffMarker(self.model)
            dropoff_marker.move_to(task.dropoff)
            self.task_markers.append(dropoff_marker)

    def update_path_markers(self):
        self.clear_markers(self.path_markers)

        for worker_id, path in self.model.token.paths.items():
            if not path:
                continue

            for cell in path[1:]:
                marker = PathMarker(self.model, worker_id)
                marker.move_to(cell)
                self.path_markers.append(marker)