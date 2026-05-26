# MAPD Toy Model

A small Python/Mesa project exploring the foundations of Multi-Agent Pickup and Delivery (MAPD).
This project implements a dynamic grid-based multi-agent environment where workers are assigned pickup and drop-off tasks generated during simulation runtime. Agents use **A\*** search to navigate an orthogonal Von Neumann grid while interacting with dynamically generated tasks and randomly generated obstacle layouts.

The project is being developed incrementally towards a full MAPF/MAPD implementation inspired by Token Passing approaches

## Features
- Mesa-based agent simulation
- CellAgent implementation
- OrthogonalVonNeumannGrid
- Von Neumann neighbourhood movement
- A* pathfinding
- Multiple independent worker agents
- Dynamic runtime task generation
- Shared FIFO task queue
- Randomised worker activation using Mesa shuffle_do()
- Random obstacle generation
- Connectivity validation for generated maps
- Automatic task assignment
- Browser visualisation using Mesa SolaraViz
- Visual obstacle rendering
- Dynamic pickup/drop-off visualisation
- Console execution support

## Running the simulation
### Browser Visualisation (Recommended)
Run the Solara application:
```bash
solara run code/app.py
```
Then open:
```bash
http://localhost:8765
```
The browser interface displays:
- worker agents
- active pickup locations
- active drop-off locations
- blocked cells
- live agent movement

### Console Mode
```bash
python code/run.py
```


## How it works
The environment is represented as a 2D orthogonal Von Neumann grid, meaning agents can move in four directions: up, down, left and right.

Each task contains:
``` bash 
pickup
dropoff
```
Tasks are generated dynamically during runtime and stored in a shared FIFO task queue.

Free agents automatically request the next available task. Agents first plan a route from their current location to the pickup cell using **A\*** search. Once the pickup location is reached, the agent replans from the pickup cell to the drop-off location.

Agents are activated using Mesa’s ``shuffle_do()`` method to reduce sequencing bias caused by fixed update ordering.

Obstacle layouts are generated randomly while ensuring that all important cells (worker start locations and task endpoints) remain reachable.

### Current Limitations
This is still an early MAPD implementation. The current implementation includes:
- multiple agents
- shared FIFO task queue
- static obstacles
- independent A* planning
- dynamic task generation
- browser visualisation

The following limitations still exist:
- no collision detection
- no collision avoidance
- no reservation table
- no space-time planning
- no cooperative planning
- no task allocation strategies
- no visualisation of planned paths
- agents may occupy the same cell simultaneously
- agents may perform edge swaps

### Future Work
Planned extensions include:
- task allocation strategies
- collision detection
- collision avoidance
- reservation tables
- space-time aware A*
- random obstacle generation
- token passing
- cooperative pathfinding
- prioritised planning
- comparison of MAPD algorithms

### Motivation
The aim of this project is to build up gradually towards a working MAPD simulation, starting from the smallest useful components: grid movement, task assignment and path planning.

The project is intended as a learning exercise in:

- agent-based simulation
- pathfinding algorithms
- multi-agent systems
- cooperative planning
- MAPD research concepts