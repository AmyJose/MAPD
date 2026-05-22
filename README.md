# MAPD Toy Model

A small Python/Mesa project exploring the foundations of Multi-Agent Pickup and Delivery (MAPD).

This currently implements a simple grid world where multiple agents are assigned pickup and drop-off tasks from a shared task queue. Agents use **A\* search** to plan routes through an orthogonal Von Neumann grid and move one cell at a time until all tasks have been completed.

## Features
- Mesa-based agent simulation
- ``CellAgent`` implementation
- ``OrthogonalVonNeumannGrid`` 
- Von Neumann neighbourhood movement
- A* pathfinding
- Static obstacle cells
- Shared FIFO task queue
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

Tasks are stored in a shared FIFO queue. When an agent completes a task, the next available task is automatically assigned until no tasks remain.

Agents are activated each simulation step using Mesa’s ``shuffle_do()`` method to reduce sequencing bias caused by fixed update ordering.

### Current Limitations
This is an early toy implementation. It currently supports:
- multiple agents
- shared FIFO task queue
- static obstacles
- independent A* planning
- no collision avoidance
- no task allocation strategies
- no dynamic replanning
- no cooperative planning
- agents may occupy the same cell simultaneously

### Future Work
Planned extensions include:
- dynamic task generation
- task allocation strategies
- collision detection
- collision avoidance
- reservation tables
- time-aware A*
- cooperative pathfinding
- prioritised planning
- visualisation using Mesa's brower interface
- comparison of MAPD algorithms

### Motivation
The aim of this project is to build up grdually towards a working MAPD simulation, starting from the smallest useful components: grid movement, task assignment and path planning

The project is intended as a learning exercise in:

- agent-based simulation
- pathfinding algorithms
- multi-agent systems
- cooperative planning
- MAPD research concepts