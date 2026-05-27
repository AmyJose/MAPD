# MAPD Toy Model

A small Python/Mesa project exploring the foundations of Multi-Agent Pickup and Delivery (MAPD).

This project implements a dynamic grid-based multi-agent environment where workers are assigned pickup and drop-off tasks generated during simulation runtime. Agents use **space-time aware A\*** search to navigate an orthogonal Von Neumann grid while interacting with dynamically generated tasks and randomly generated obstacle layouts.

The project is being developed incrementally towards a full MAPF/MAPD implementation inspired by Token Passing approaches.


# Features

- Mesa-based agent simulation
- `CellAgent` implementation
- `OrthogonalVonNeumannGrid`
- Von Neumann neighbourhood movement
- Space-time aware A\* pathfinding
- Multiple independent worker agents
- Dynamic runtime task generation
- Early Token Passing architecture
- Shared system token for:
  - task ownership
  - worker assignments
  - planned paths
  - reservation tracking
- Randomised worker activation using Mesa `shuffle_do()`
- Random obstacle generation
- Connectivity validation for generated maps
- Reservation table infrastructure
- Cell reservation tracking
- Edge reservation tracking
- Wait actions during planning
- Browser visualisation using Mesa SolaraViz
- Visual obstacle rendering
- Dynamic pickup/drop-off visualisation
- Planned path visualisation
- Collision detection
- Vertex collision detection
- Edge-swap collision detection
- Worker ID tracking
- Simulation metrics collection using Mesa `DataCollector`
- Timestamped simulation result exporting
- File-based logging and debugging support
- Task completion statistics
- Console execution support

# Running the Simulation

## Browser Visualisation (Recommended)

Run the Solara application:

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

Simulation outputs are automatically saved into timestamped directories inside `results/`.

Generated outputs include:

- model-level metrics CSVs
- agent-level metrics CSVs
- simulation log files

Example structure:

```text
results/
├── 20260527_193055/
│   ├── model_data.csv
│   ├── agent_data.csv
│   └── simulation.log
```

Logging currently includes:

- task generation
- token interactions
- task assignment
- reservation updates
- reservation conflicts
- agent movement
- path planning
- collision events
- worker state transitions



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

Idle workers request access to the token and attempt to claim an available task. Once assigned, workers independently plan routes using **space-time aware A\*** search.

Agents first plan a route from their current location to the pickup cell. Once the pickup location is reached, the agent replans from the pickup cell to the drop-off location.

The planner reasons over both:

- spatial position
- timestep

This allows the simulation to reason about future conflicts and reserved space-time occupancy.

Workers reserve:

- future occupied cells
- traversed edges
- temporary goal occupancy

The token currently stores:

- active tasks
- worker-task assignments
- planned paths
- reservation tables

Agents are activated using Mesa’s `shuffle_do()` method to reduce sequencing bias caused by fixed update ordering.

Obstacle layouts are generated randomly while ensuring that all important cells (worker start locations and task endpoints) remain reachable.

# Collision Detection and Reservations

The simulation currently detects:

- vertex collisions
- edge-swap collisions

The reservation system is used to reduce future conflicts during path planning.

Workers check reservations before expanding future states during A\* search. Paths that would violate reserved cells or reserved edge transitions are rejected during planning.

The reservation system is still experimental and does not yet fully guarantee collision-free execution.

# Current Limitations

This is still an early MAPD implementation. The current implementation includes:

- multiple agents
- token-based task ownership
- dynamic task generation
- random obstacle generation
- connectivity validation
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
- no advanced task allocation strategies
- reservations may become stale after replanning
- agents may still occupy the same cell simultaneously
- agents may still perform edge swaps
- planning is currently decentralised and greedy

# Future Work

Planned extensions include:

- robust collision avoidance
- prioritised planning
- full Token Passing implementation
- cooperative pathfinding
- reservation expiry systems
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

The project is intended as a learning exercise in:

- agent-based simulation
- pathfinding algorithms
- multi-agent systems
- cooperative planning
- MAPF/MAPD research concepts