import mesa
from mesa.discrete_space import OrthogonalVonNeumannGrid
from agent import WorkerAgent
from markers import ParkingMarker, BlockedCellMarker
from system_token import SystemToken, Task
import logging
from scenario import build_scenario

logger = logging.getLogger(__name__)

class SpaceModel(mesa.Model):
    """a model containing some number of agents that move around a grid"""
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
            show_markers=True,
        ):
        
        super().__init__(seed=seed)

        self.scenario_name = scenario
        self.show_markers = show_markers

        #for fixed size scenariod, override before creating grid
        width, height = self.get_gris_size_for_scenario(
            scenerio=scenario,
            width=width,
            height=height
        )

        self.width = width
        self.height = height

        self.grid = OrthogonalVonNeumannGrid(
            [width, height],
            torus=False, 
            random=self.random
        )

        self.token = SystemToken()
        self.workers = []

        # model counters
        self.vertex_collisions = 0
        self.edge_collisions = 0
        self.completed_tasks = 0
        self.generated_tasks = 0

        scenario_config = build_scenario(
            name=scenario,
            grid=self.grid,
            rng=self.random,
            width=width,
            height=height,
            num_workers=num_workers,
            num_task_endpoints=num_task_endpoints,
            blocked_spawn_probability=blocked_spawn_probability,
            task_spawn_probability=task_spawn_probability,
            max_tasks_waiting=max_tasks_waiting,
        )

        self.apply_scenario(scenario_config)
        self.create_workers()
        self.initialise_token()

        if self.show_markers:
            self.create_static_markers()

        if self.scenario_name == "test":
            self.create_test_tasks()

        self.datacollector = self.create_datacollector()

    def get_grid_size_for_scenario(self, scenario, width, height):
        if scenario == "test":
            return 5, 3

        if scenario == "warehouse":
            return 35, 21

        if scenario == "standard":
            return 10, 10

        return width, height

    def apply_scenario(self, scenario_config):
        self.width = scenario_config.width
        self.height = scenario_config.height
        self.num_workers = scenario_config.num_workers
        self.task_spawn_probability = scenario_config.task_spawn_probability
        self.max_tasks_waiting = scenario_config.max_tasks_waiting

        self.start_cells = scenario_config.start_cells
        self.task_endpoints = scenario_config.task_endpoints
        self.resting_endpoints = scenario_config.resting_endpoints
        self.blocked_cells = scenario_config.blocked_cells

        self.endpoints = scenario_config.endpoints

    def create_workers(self):
        for worker_id, cell in enumerate(self.start_cells):
            worker = WorkerAgent(self, worker_id=worker_id)
            worker.move_to(cell)
            self.workers.append(worker)

    def initialise_token(self):
        token = self.token
        # assign trivial paths
        for worker in self.workers:
            token.paths[worker.worker_id] = [worker.cell]

    def create_static_markers(self):
        for cell in self.resting_endpoints:
            marker = ParkingMarker(self)
            marker.move_to(cell)

        for cell in self.blocked_cells:
            marker = BlockedCellMarker(self)
            marker.move_to(cell)

    def step(self):
        previous_positions = {
            worker: worker.cell
            for worker in self.workers
        }

        self.maybe_generate_task()

        for worker in self.workers:
            worker.step()

        for worker in self.workers:
            worker.move()

        self.detect_collisions(previous_positions)
        self.datacollector.collect(self)

    def maybe_generate_task(self):
        if self.scenario_name == "test":
            return

        if len(self.token.tasks) >= self.max_tasks_waiting:
            return

        if self.random.random() > self.task_spawn_probability:
            return

        pickup = self.random.choice(self.task_endpoints)
        dropoff = self.random.choice(self.task_endpoints)

        while dropoff == pickup:
            dropoff = self.random.choice(self.task_endpoints)

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
                worker_ids = [worker.worker_id for worker in workers]

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
                    worker.task is not None for worker in m.workers
                ),
                "Idle Workers": lambda m: sum(
                    worker.task is None for worker in m.workers
                ),
            },
            agent_reporters={
                "Agent Type": lambda a: type(a).__name__,
                "Worker ID": lambda a: getattr(a, "worker_id", None),
                "Has Task": lambda a: getattr(a, "task", None) is not None,
                "Cell": lambda a: a.cell.coordinate if a.cell else None,
            },
        )