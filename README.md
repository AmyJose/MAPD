# MAPD Toy Model

A small Python/Mesa project exploring the foundations of Multi-Agent Pickup and Delivery (MAPD).

This currently implements a simple grid world where a robot agent is assigned a task with a piclup and drop-off location. The agent uses **A\* search** to plan a route through an orthogonal Von Neumann grid and moves one cell at a time until the task is completed.

## Features
- Mesa-based agent simulation
- ``CellAgent`` implementation
- ``OrthogonalVonNeumannGrid`` 
- Von Neumann neighbourhood movement
- A* pathfinding
- Static obstacle cells
- Pickup and drop-off task structure
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

A task contains
``` bash 
pickup
dropoff
```
The robot first plans a path from its current cell to the pickup cell using A*. Once it reaaches the pickup, it replans from the pickup cell to the drop-off cell. When it reaches the drop-off location, the task is completed.

### Current Limitations
This is an early toy implementation. It currently supports:
- one agent
- one task at a time
- static obstacles
- no collision avoidance
- no task allocation
- no dynamic replanning

### Future Work
Planned extensions include:
- multiple agents
- multiple tasks
- task allocation strategies
- collision avoidance
- reservation tables
- dynamic task generation
- visualisation using Mesa's brower interface
- comparison of MAPD algorithms

### Motivation
The aim of this project is to build up grdually towards a working MAPD simulation, starting from the smallest useful components: grid movement, task assignment and path planning