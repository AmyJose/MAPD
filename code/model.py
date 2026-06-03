import logging
from collections import deque

import mesa
from mesa.discrete_space import OrthogonalVonNeumannGrid

from agent import WorkerAgent
from display_layer import DisplayLayer
from scenario import build_scenario
from system_token import SystemToken, Task

logger = logging.getLogger(__name__)


class SpaceModel(mesa.Model):
    """MAPD model using token passing."""

    def __init__(
        self,
        width=10,
        height=10,
        seed=None,
        scenario="random",
        num_workers=3,
        num_task_endpoints=8,
        blocked_spawn_probability=0.15,
        task_spawn_probability=0.2,
        max_tasks_waiting=5,
        show_display=True,
    ):
        super().__init__(seed=seed)

        self.scenario = scenario
        self.show_display = show_display

        width, height = self.get_grid_size_for_scenario(
            scenario=scenario,
            width=width,
            height=height,
        )

        self.width = width
        self.height = height

        self.grid = OrthogonalVonNeumannGrid(
            [self.width, self.height],
            torus=False,
            random=self.random,
        )

        self.problem = build_scenario(
            name=scenario,
            grid=self.grid,
            rng=self.random,
            num_workers=num_workers,
            num_task_endpoints=num_task_endpoints,
            blocked_spawn_probability=blocked_spawn_probability,
        )

        self.task_spawn_probability = task_spawn_probability
        self.max_tasks_waiting = max_tasks_waiting

        if scenario == "test":
            self.task_spawn_probability = 0.0
            self.max_tasks_waiting = 2

        if scenario == "warehouse":
            self.task_spawn_probability = 0.2
            self.max_tasks_waiting = 20

        self.token = SystemToken()
        self.workers = []

        self.generated_tasks = 0
        self.completed_tasks = 0
        self.vertex_collisions = 0
        self.edge_collisions = 0

        self.create_workers()
        self.initialise_token()
        self.endpoint_distances = self.precompute_endpoint_distances()

        self.display = DisplayLayer(self)

        if self.show_display:
            self.display.create_static_markers()

        if self.scenario == "test":
            self.create_test_tasks()

        self.datacollector = self.create_datacollector()

    @staticmethod
    def get_grid_size_for_scenario(scenario, width, height):
        if scenario == "test":
            return 5, 3

        if scenario == "standard":
            return 10, 10

        if scenario == "warehouse":
            return 35, 21

        return width, height

    @property
    def endpoints(self):
        return self.problem.endpoints

    @property
    def task_endpoints(self):
        return self.problem.task_endpoints

    @property
    def resting_endpoints(self):
        return self.problem.resting_endpoints

    @property
    def blocked_cells(self):
        return self.problem.blocked_cells

    @property
    def start_cells(self):
        return self.problem.start_cells

    def create_workers(self):
        for worker_id, cell in enumerate(self.problem.start_cells):
            worker = WorkerAgent(self, worker_id=worker_id)
            worker.move_to(cell)
            self.workers.append(worker)

    def initialise_token(self):
        for worker in self.workers:
            self.token.paths[worker.worker_id] = [worker.cell]

    def precompute_endpoint_distances(self):
        """
        For each endpoint, compute shortest path distance from every reachable cell
        to that endpoint, respecting blocked cells.

        Returns:
            dict: endpoint -> {cell -> distance}
        """
        distances = {}

        for endpoint in self.endpoints:
            distances[endpoint] = self.bfs_distances_from(endpoint)

        return distances


    def bfs_distances_from(self, start_cell):
        distances = {start_cell: 0}
        frontier = deque([start_cell])

        while frontier:
            current = frontier.popleft()

            for neighbour in current.neighborhood:
                if neighbour in self.blocked_cells:
                    continue

                if neighbour in distances:
                    continue

                distances[neighbour] = distances[current] + 1
                frontier.append(neighbour)

        return distances


    def h_value(self, from_cell, endpoint):
        """
        Obstacle-aware shortest path distance from from_cell to endpoint.
        """
        return self.endpoint_distances.get(endpoint, {}).get(from_cell, float("inf"))

    def step(self):
        previous_positions = {
            worker: worker.cell
            for worker in self.workers
        }

        self.maybe_generate_task()

        for worker in self.workers:
            if worker.has_reached_end_of_token_path():
                worker.step()

        if self.show_display:
            self.display.update()

        for worker in self.workers:
            worker.move()

        if self.show_display:
            self.display.update()

        self.detect_collisions(previous_positions)
        self.datacollector.collect(self)

    def maybe_generate_task(self):
        if self.scenario == "test":
            return

        if len(self.token.tasks) >= self.max_tasks_waiting:
            return

        if self.random.random() > self.task_spawn_probability:
            return

        pickup = self.random.choice(list(self.problem.task_endpoints))
        dropoff = self.random.choice(list(self.problem.task_endpoints))

        while dropoff == pickup:
            dropoff = self.random.choice(list(self.problem.task_endpoints))

        task = Task(
            pickup=pickup,
            dropoff=dropoff,
        )

        self.token.add_task(task)
        self.generated_tasks += 1

        logger.info(
            f"[t={self.steps}] Generated task: "
            f"{pickup.coordinate} -> {dropoff.coordinate}"
        )

    def create_test_tasks(self):
        task_0 = Task(
            pickup=self.grid[(0, 1)],
            dropoff=self.grid[(4, 1)],
        )

        task_1 = Task(
            pickup=self.grid[(4, 1)],
            dropoff=self.grid[(0, 1)],
        )

        self.token.add_task(task_0)
        self.token.add_task(task_1)
        self.generated_tasks += 2

    def detect_collisions(self, previous_positions):
        self.detect_vertex_collisions()
        self.detect_edge_collisions(previous_positions)

    def detect_vertex_collisions(self):
        occupied = {}

        for worker in self.workers:
            cell = worker.cell
            occupied.setdefault(cell, []).append(worker)

        for cell, workers in occupied.items():
            if len(workers) > 1:
                self.vertex_collisions += 1

                worker_ids = [
                    worker.worker_id
                    for worker in workers
                ]

                logger.warning(
                    f"[t={self.steps}] Vertex collision at "
                    f"{cell.coordinate}: workers {worker_ids}"
                )

    def detect_edge_collisions(self, previous_positions):
        moves = {
            worker: (previous_positions[worker], worker.cell)
            for worker in self.workers
        }

        checked_pairs = set()

        for worker_a, move_a in moves.items():
            for worker_b, move_b in moves.items():
                if worker_a == worker_b:
                    continue

                pair = frozenset({worker_a, worker_b})

                if pair in checked_pairs:
                    continue

                checked_pairs.add(pair)

                a_start, a_end = move_a
                b_start, b_end = move_b

                if (
                    a_start != a_end
                    and b_start != b_end
                    and a_start == b_end
                    and b_start == a_end
                ):
                    self.edge_collisions += 1

                    logger.warning(
                        f"[t={self.steps}] Edge collision: "
                        f"{a_start.coordinate} <-> {a_end.coordinate} "
                        f"between {worker_a.worker_id} and {worker_b.worker_id}"
                    )

    def create_datacollector(self):
        return mesa.DataCollector(
            model_reporters={
                "Generated Tasks": "generated_tasks",
                "Completed Tasks": "completed_tasks",
                "Waiting Tasks": lambda m: len(m.token.tasks),
                "Vertex Collisions": "vertex_collisions",
                "Edge Collisions": "edge_collisions",
                "Active Workers": lambda m: sum(
                    worker.task is not None
                    for worker in m.workers
                ),
                "Idle Workers": lambda m: sum(
                    worker.task is None
                    for worker in m.workers
                ),
            },
            agent_reporters={
                "Agent Type": lambda a: type(a).__name__,
                "Worker ID": lambda a: getattr(a, "worker_id", None),
                "Carrying": lambda a: getattr(a, "carrying", None),
                "Has Task": lambda a: getattr(a, "task", None) is not None,
                "Cell": lambda a: (
                    a.cell.coordinate
                    if getattr(a, "cell", None)
                    else None
                ),
                "Token Path Length": lambda a: (
                    len(a.model.token.paths.get(a.worker_id, []))
                    if hasattr(a, "worker_id")
                    else None
                ),
            },
        )