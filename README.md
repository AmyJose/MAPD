# MAPD Toy Model

A small Python/Mesa project exploring the foundations of Multi-Agent Pickup and Delivery (MAPD).

This currently implements a simple grid world where a robot agent is assigned a queue of pickup and drop-off tasks. The agent uses **A\* search** to plan a route through an orthogonal Von Neumann grid and moves one cell at a time until all tasks have been completed.

## Features
- Mesa-based agent simulation
- ``CellAgent`` implementation
- ``OrthogonalVonNeumannGrid`` 
- Von Neumann neighbourhood movement
- A* pathfinding
- Static obstacle cells
- Pickup and drop-off task system
- Task queue support
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
The agent first plans a path from its current cell to the pickup location using A*. Once the pickup location is reached, the agent replans from the pickup cell to the drop-off location.

Tasks are stored in a queue. When a task is completed, the next available task is automatically assigned to the agent until no tasks remain.

### Current Limitations
This is an early toy implementation. It currently supports:
- one agent
- FIFO task queue
- static obstacles
- no collision avoidance
- no task allocation strategies
- no dynamic replanning
- no multi-agent coordination

### Future Work
Planned extensions include:
- multiple agents
- dynamic task generation
- task allocation strategies
- collision avoidance
- reservation tables
- time-aware A*
- cooperative pathfinding
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