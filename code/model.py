import mesa
from mesa.discrete_space import OrthogonalVonNeumannGrid
from agent import WorkerAgent
from markers import PickupMarker, BlockedCellMarker
from system_token import SystemToken, Task
import logging

logger = logging.getLogger(__name__)

class SpaceModel(mesa.Model):
    """a model containing some number of agents that move around a grid"""
    def __init__(self, width = 10, height = 10, seed=None):
        super().__init__(seed=seed)

        self.grid = OrthogonalVonNeumannGrid((width, height), torus=False, random=self.random)

        self.blocked_spawn_probability = 0.15
        self.num_workers = 3
        self.num_task_endpoints = 8
        self.task_spawn_probability = 0.2

        self.token = SystemToken()
        self.workers = []

        # model counters
        self.vertex_collisions = 0
        self.edge_collisions = 0
        self.completed_tasks = 0
        self.generated_tasks = 0

        self.start_cells = self.generate_random_cells(self.num_workers)
        for i, cell in enumerate(self.start_cells):
            worker = WorkerAgent(self, worker_id=i)
            worker.move_to(cell)
            self.workers.append(worker)

        self.task_endpoints = self.generate_random_cells(self.num_task_endpoints, forbidden=set(self.start_cells))

        self.blocked_cells = self.generate_valid_blocked_cells(forbidden = set(self.start_cells) | set(self.task_endpoints))
        for cell in self.blocked_cells:
            block = BlockedCellMarker(self)
            block.move_to(cell)

        
        #data collectors for run stats
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Generated Tasks": "generated_tasks",
                "Completed Tasks": "completed_tasks",
                "Waiting Tasks" : lambda m : len(m.token.tasks),
                "Vertex Collisions": "vertex_collisions",
                "Edge Collisions": "edge_collisions",
                "Active Workers": lambda m: sum(worker.task is not None for worker in m.workers),
                "Idle Workers" : lambda m: sum(worker.task is None for worker in m.workers),
            },
            agent_reporters={
                "Agent Type": lambda a: type(a).__name__,
                "Worker ID": lambda a: getattr(a, "worker_id", None),
                "Carrying": lambda a: getattr(a, "carrying", None),
                "Has Task": lambda a: getattr(a, "task", None) is not None,
                "Path Length": lambda a: len(getattr(a, "path", [])),
                "Cell": lambda a: a.cell.coordinate if a.cell else None,
            }
        )

    def step(self):
        """Advance by one step"""

        #keep track of the previous positions of all agents
        previous_positions = {
            worker: worker.cell
            for worker in self.workers
        }
        self.maybe_generate_task()

        #self.reserve_idle_workers(self.steps)
        
        for worker in self.workers:
            if worker.task is None:
                worker.request_token()

        self.agents.shuffle_do("step")
        
        self.detect_collisions(previous_positions)
        self.datacollector.collect(self)

    def detect_collisions(self, previous_positions):
        self.detect_vertex_collisions()
        self.detect_edge_collisions(previous_positions)

    def detect_vertex_collisions(self):
        #dictionary holding all worker positions
        #structure: [x, y] : worker
        occupied = {}
        for worker in self.workers:
            cell = worker.cell
            if cell not in occupied:
                occupied[cell] = [worker]
            else:
                occupied[cell].append(worker)

        #loop through and checkkk
        # if a cell [x, y] has more than one entry, there is collision
        for cell, workers in occupied.items():
            if len(workers)> 1:
                self.vertex_collisions += 1
                worker_ids = [worker.worker_id for worker in workers]

                logger.warning(
                    f"[t={self.steps}] Vertex collision at "
                    f"{cell.coordinate}: workers {worker_ids}"
                )
    
    # edge swaps!
    def detect_edge_collisions(self, previous_positions):
        moves = {}
        for worker in self.workers:
            start = previous_positions[worker]
            end = worker.cell
            moves[worker] = (start, end)

        #avoid double counting
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

                if a_start == b_end and b_start == a_end:
                    self.edge_collisions += 1

                    logger.warning(
                        f"[t={self.steps}] Edge collision: "
                        f"{a_start.coordinate} <-> {a_end.coordinate} "
                        f"between {worker_a.worker_id} and {worker_b.worker_id}"
                    )  

    # task generator
    def maybe_generate_task(self):
        if self.random.random() > self.task_spawn_probability:
            return
        
        pickup = self.random.choice(self.task_endpoints)
        dropoff = self.random.choice(self.task_endpoints)

        while dropoff == pickup:
            dropoff = self.random.choice(self.task_endpoints)

        task = Task(pickup=pickup, dropoff=dropoff)
        self.token.add_task(task)
        self.generated_tasks += 1

        logger.info(
            f"[t={self.steps}] Generated task: "
            f"{pickup.coordinate} -> {dropoff.coordinate}"
        )
    
    def generate_valid_blocked_cells(self, forbidden=None, max_attempts=100):
        forbidden = forbidden or set()
        for _ in range(max_attempts):
            blocked_cells = self.generate_blocked_cells(forbidden=forbidden)

            if self.is_connected_for_problem(blocked_cells):
                return blocked_cells
        raise RuntimeError(
            "Could not generate a connected obstacle layout. "
            "Try reducing obstacle_probability."
        )

    def generate_blocked_cells(self, forbidden=None):
        forbidden = forbidden or set()

        blocked_cells = set()

        for cell in self.grid.all_cells:
            if cell in forbidden:
                continue
            if self.random.random() < self.blocked_spawn_probability:
                blocked_cells.add(cell)

        return blocked_cells
    
    def generate_random_cells(self, count, forbidden=None):
        forbidden = forbidden or set()

        available_cells = [
            cell for cell in self.grid.all_cells
            if cell not in forbidden
        ]

        if count > len(available_cells):
            raise ValueError("Not enough available cells to sample from")
        
        return self.random.sample(available_cells, count)
    
    #DFS to ensure all tasks are connected
    def get_reachable_cells(self, start_cell, blocked_cells):
        visited = set()
        frontier = [start_cell]

        while frontier:
            current = frontier.pop()

            if current in visited:
                continue

            visited.add(current)

            for neighbour in current.neighborhood:
                if neighbour in blocked_cells:
                    continue

                if neighbour not in visited:
                    frontier.append(neighbour)

        return visited
    
    def is_connected_for_problem(self, blocked_cells):
        important_cells = set(self.start_cells) | set(self.task_endpoints)

        if not important_cells:
            return True
        
        first_cell = next(iter(important_cells))
        reachable_cells = self.get_reachable_cells(first_cell, blocked_cells)

        return important_cells.issubset(reachable_cells)
    
    def debug_reservations(self, cell, horizon=10):
        logger.debug(
            f"Reservations for {cell.coordinate}:"
        )

        for t in range(self.steps, self.steps + horizon):
            owner = self.token.reserved_cells.get((cell, t))

            if owner is not None:
                logger.debug(
                    f"  t={t}: worker {owner}"
                )
    