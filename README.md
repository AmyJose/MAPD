# MAPD Toy Model

A small Python/Mesa project exploring the foundations of Multi-Agent Pickup and Delivery (MAPD).

This project implements a dynamic grid-based multi-agent environment where workers are assigned pickup and drop-off tasks generated during simulation runtime. Agents use **space-time aware A\*** search to navigate an orthogonal Von Neumann grid while interacting with dynamically generated tasks, randomly generated obstacle layouts, and token-managed reservations.

The project is being developed incrementally towards a full MAPF/MAPD implementation inspired by Token Passing approaches.


# Features

- Mesa-based agent simulation
- `CellAgent` implementation
- `OrthogonalVonNeumannGrid`
- Space-time aware A\* pathfinding
- Multiple independent worker agents
- Dynamic runtime task generation
- Shared system token for:
  - task storage
  - worker-task assignments
  - planned paths
  - cell reservations
  - edge reservations
  - parking assignments
- Closest-completion-cost task selection
- Token-managed parking behaviour for idle workers
- Parking reservation refreshing
- Reservation cleanup for old timesteps
- Random obstacle generation
- Connectivity validation for starts, task endpoints, and parking cells
- Browser visualisation using Mesa SolaraViz
- Dynamic pickup/drop-off visualisation
- Planned path visualisation
- Vertex and edge-swap collision detection
- Worker ID tracking
- Simulation metrics collection using Mesa `DataCollector`
- Timestamped simulation result exporting
- File-based logging and debugging support

# Running the Simulation

## Browser Visualisation

```bash
solara run code/app.py
```

Then open:

```text
http://localhost:8765
```

The browser interface displays:

- worker agents
- active pickup locations
- active drop-off locations
- blocked cells
- planned agent paths
- live agent movement

## Console Mode

```bash
python code/run.py
```
# Results and Logging

Simulation outputs are saved into timestamped directories inside `results/`.

Generated outputs may include:

- model-level metrics CSVs
- agent-level metrics CSVs
- simulation log files

Logging currently includes:

- task generation
- token interactions
- task assignment
- reservation updates
- reservation conflicts
- worker movement
- path planning
- collision events
- parking behaviour


# How It Works

The environment is represented as a 2D orthogonal Von Neumann grid, meaning agents can move in four directions:

- up
- down
- left
- right

Each task contains:

```text
pickup
dropoff
```

Tasks are generated dynamically during runtime and stored inside a shared system token.

Idle workers request the token. If tasks are available, workers evaluate reachable tasks using estimated full completion cost:

```text
cost = path to pickup + path from pickup to drop-off
```

The worker claims the task with the lowest estimated completion cost, plans a path to the pickup location, and records its assignment and reservations in the token.

If no suitable task is available, the worker moves to a token-managed parking cell. Parking cells are assigned through the token to avoid multiple idle workers selecting the same parking location.

The planner reasons over both:

- spatial position
- timestep

Workers reserve:

- future occupied cells
- traversed edges
- temporary goal occupancy
- assigned parking cells

Old reservations are periodically cleared, while parking reservations are refreshed to keep parked workers protected.

# Collision Detection and Reservations

The simulation currently detects:

- vertex collisions
- edge-swap collisions

The reservation system is used to reduce future conflicts during path planning. Workers check reserved cells, reserved edges, and occupied parking cells before expanding future A\* states.

The reservation system is still experimental and does not yet fully guarantee collision-free execution.

# Current Limitations

This is still an early MAPD implementation. The current implementation includes:

- multiple agents
- dynamic task generation
- token-based task ownership
- token-managed parking
- independent space-time A\* planning
- reservation-table infrastructure
- browser visualisation
- collision detection
- simulation data collection
- logging/debugging support

The following limitations still exist:

- collision avoidance is not yet fully reliable
- no cooperative replanning
- no prioritised planning
- token passing is still partial/incomplete
- no advanced task allocation strategy beyond estimated completion cost
- agents may still occupy the same cell simultaneously
- agents may still perform edge swaps
- planning is currently decentralised and greedy

# Future Work

Planned extensions include:

- robust collision avoidance
- prioritised planning
- full Token Passing implementation
- cooperative pathfinding
- rolling horizon planning
- smarter task allocation strategies
- congestion visualisation
- reservation visualisation
- MAPF/MAPD algorithm comparison
- performance benchmarking


# Motivation

The aim of this project is to gradually build towards a working MAPF/MAPD simulation, starting from the smallest useful components:

- grid movement
- task assignment
- path planning
- dynamic task generation
- multi-agent coordination
- reservation-based planning
- token-based coordination
- parking/endpoint management

The project is intended as a learning exercise in:

- agent-based simulation
- pathfinding algorithms
- multi-agent systems
- cooperative planning
- MAPF/MAPD research concepts