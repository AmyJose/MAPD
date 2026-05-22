# MAPD Toy Model

A small Python/Mesa project exploring the foundations of Multi-Agent Pickup and Delivery (MAPD).

This currently implements a simple grid world where multiple agents are dynamically assigned pickup and drop-off tasks from a shared task queue. Tasks are generated during simulation runtime, and agents use**A* search** to plan routes through an orthogonal Von Neumann grid.

## Features
- Mesa-based agent simulation
- ``CellAgent`` implementation
- ``OrthogonalVonNeumannGrid`` 
- Von Neumann neighbourhood movement
- A* pathfinding
- Static obstacle cells
- Shared FIFO task queue
- Dynamic task generation
- Multiple independent agents
- Randomised agent activation using Mesa ``shuffle_do()``
- Automatic task assignment
- Console-based grid visualisation

## Running the simulation
``` bash
python code/run.py
```
The console output shows the grid at each step:
``` bash
A = agent
P = pickup location
D = drop-off location
# = blocked cell
. = empty cell
```

## How it works
The model creates a 2D orthogonal Von Neumann grid, meaning agents can move in four directions: up, down, left and right.

Each task contains
``` bash 
pickup
dropoff
```
Agents first plan a path from their current cell to the pickup location using A*. Once the pickup location is reached, the agent replans from the pickup cell to the drop-off location.

Tasks are dynamically generated during runtime and stored in a shared FIFO queue. Free agents automatically request the next available task from the queue. Once a task is completed, the agent becomes available to receive another task.

Agents are activated each simulation step using Mesa’s ``shuffle_do()`` method to reduce sequencing bias caused by fixed update ordering.

### Current Limitations
This is an early toy implementation. It currently supports:
- multiple agents
- shared FIFO task queue
- static obstacles
- independent A* planning
- no collision avoidance
- no task allocation strategies
- no collision detection
- no cooperative planning
- agents may occupy the same cell simultaneously

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
- visualisation using Mesa's browser interface
- comparison of MAPD algorithms

### Motivation
The aim of this project is to build up gradually towards a working MAPD simulation, starting from the smallest useful components: grid movement, task assignment and path planning

The project is intended as a learning exercise in:

- agent-based simulation
- pathfinding algorithms
- multi-agent systems
- cooperative planning
- MAPD research concepts