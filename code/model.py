import mesa
from mesa.discrete_space import OrthogonalVonNeumannGrid
from agent import WorkerAgent
from dataclasses import dataclass
from markers import PickupMarker, BlockedCellMarker
from token import Token
import logging

#what a task is:
@dataclass
class Task:
    pickup: tuple[int, int]
    dropoff: tuple [int,int]
    pickup_marker: object = None
    dropoff_marker: object = None

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

        self.token = Token()
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
                "Waiting Tasks" : lambda m : len(m.tasks),
                "Vertex Collisions": "vertex_collisions",
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

        self.reserve_idle_workers(self.steps)
        
        for worker in self.workers:
            if worker.task is None:
                self.assign_next_task(worker)

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
    
    # goes through the path and reserves edges at the time they appear
    def reserve_path(self, worker, path, start_time, goal_reserve_horizon=2):
        logger.debug(
            f"[t={start_time}] Reserving path for "
            f"worker {worker.worker_id}"
        )
        previous_cell = worker.cell

        for i, cell in enumerate(path):
            timestep = start_time + i + 1

            logger.debug(
                f"  reserve cell {cell.coordinate} "
                f"at t={timestep}"
            )

            self.reserved_cells[(cell, timestep)] = worker
            self.reserved_edges[(previous_cell, cell, timestep)] = worker
            previous_cell = cell

        #keep the final cell reserved for a bit after arrival
        #stops another agent planning into a workers end immediately after the path ends
        if path:
            final_cell = path[-1]
        else:
            final_cell = worker.cell

        final_time = start_time + len(path)

        for t in range(final_time + 1, final_time + goal_reserve_horizon +1):
            self.reserved_cells[(final_cell, t)] = worker

    def assign_next_task(self, agent):
        if not self.tasks:
            return
        
        next_task = self.tasks.pop(0)
        agent.assign_task(next_task)

        pickup_marker = PickupMarker(self)
        pickup_marker.move_to(next_task.pickup)
        next_task.pickup_marker = pickup_marker

        logger.info(
            f"[t={self.steps}] Worker {agent.worker_id} "
            f"assigned task: "
            f"{next_task.pickup.coordinate} -> "
            f"{next_task.dropoff.coordinate}"
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
    
    def clear_reservations_for(self, worker):
        self.reserved_cells = {
            key: value
            for key, value in self.reserved_cells.items()
            if value is not worker
        }
        self.reserved_edges = {
            key: value
            for key, value in self.reserved_edges.items()
            if value is not worker
        }

    def reserve_idle_workers(self, start_time, horizon=20):
        for worker in self.workers:
            if worker.task is None:
                for t in range(start_time + 1, start_time + horizon + 1):
                    self.reserved_cells[(worker.cell, t)] = worker
    
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

    def is_cell_reserved(self, cell, timestep, worker=None):
        reserved_by=self.reserved_cells.get((cell, timestep))
        return reserved_by is not None and reserved_by is not worker
    
    def is_edge_reserved(self, from_cell, to_cell, timestep):
        return (from_cell, to_cell, timestep) in self.reserved_edges
    
    def would_swap_edges(self, from_cell, to_cell, timestep, worker=None):
        reserved_by= self.reserved_edges.get((to_cell, from_cell, timestep))
        return reserved_by is not None and reserved_by is not worker
    
    def debug_reservations(self, cell, horizon=10):
        logger.debug(
            f"Reservations for {cell.coordinate}:"
        )

        for t in range(self.steps, self.steps + horizon):
            owner = self.reserved_cells.get((cell, t))

            if owner is not None:
                logger.debug(
                    f"  t={t}: worker {owner.worker_id}"
                )
    