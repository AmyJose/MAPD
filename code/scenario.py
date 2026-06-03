from problem_instance import ProblemInstance

def build_scenario(
        name,
        grid,
        rng,
        num_workers=3,
        num_task_endpoints=8,
        blocked_spawn_probability=0.15,
    ):
    if name == "standard":
        return build_standard_scenario(grid)

    if name == "test":
        return build_test_scenario(grid)
    
    if name == "warehouse":
        return build_warehouse_scenario(grid, rng)
    
    if name == "random":
        return build_random_scenario(
            grid=grid,
            rng=rng,
            num_workers=num_workers,
            num_task_endpoints=num_task_endpoints,
            blocked_spawn_probability=blocked_spawn_probability,
        )
    
    raise ValueError(f"Unknown scenario: {name}")

def build_standard_scenario(grid):
    start_cells = [
        grid[(0, 0)],
        grid[(5, 0)],
        grid[(9, 0)],
    ]

    task_endpoints = [
        grid[(2, 0)],
        grid[(1, 4)],
        grid[(0, 8)],
        grid[(1, 9)],
        grid[(5, 7)],
        grid[(8, 4)],
        grid[(9, 4)],
        grid[(8, 8)],
    ]

    resting_endpoints = [
        grid[(3, 9)],
        grid[(4, 9)],
        grid[(5, 9)],
    ]

    blocked_cells = {
        grid[(2, 3)],
        grid[(2, 4)],
        grid[(3, 3)],
        grid[(3, 4)],
        grid[(7, 1)],
        grid[(0, 6)],
        grid[(1, 6)],
        grid[(2, 6)],
        grid[(8, 5)],
        grid[(8, 6)],
        grid[(9, 5)],
        grid[(9, 6)],
    }

    return ProblemInstance(
        start_cells=start_cells,
        task_endpoints=task_endpoints,
        resting_endpoints=resting_endpoints,
        blocked_cells=blocked_cells,
    )

def build_test_scenario(grid):
    start_cells = [
        grid[(0, 1)],
        grid[(4, 1)],
    ]

    task_endpoints = [
        grid[(0, 1)],
        grid[(4, 1)],
    ]

    resting_endpoints = [
        grid[(4, 2)],
        grid[(2, 2)],
        grid[(4, 0)],
    ]

    blocked_cells = {
        grid[(x, y)]
        for x in range(5)
        for y in range(3)
        if y != 1 and (x, y) not in {(4, 2), (4, 0)}
    }

    return ProblemInstance(
        start_cells=start_cells,
        task_endpoints=task_endpoints,
        resting_endpoints=resting_endpoints,
        blocked_cells=blocked_cells,
    )

def build_warehouse_scenario(grid, rng):
    num_workers = 50

    start_cells = []
    task_endpoints = []
    blocked_cells = set()

    shelf_y_values = [2, 6, 10, 14, 18]

    for y in shelf_y_values:
        #finishes at 16
        for x in range(7, 17):
            blocked_cells.add(grid[(x, y)])

        for x in range(18, 28):
            blocked_cells.add(grid[(x, y)])

    endpoint_columns = [1, 2, 4, 5, 29, 30, 32, 33]

    for x in endpoint_columns:
        for y in range(1, 20):
            cell = grid[(x, y)]

            if cell not in blocked_cells:
                task_endpoints.append(cell)

    for y in [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]:
        for x in range(7, 17):
            cell = grid[(x, y)]

            if cell not in blocked_cells:
                task_endpoints.append(cell)

        for x in range(18, 28):
            cell = grid[(x, y)]

            if cell not in blocked_cells:
                task_endpoints.append(cell)

    task_endpoints = remove_duplicates(task_endpoints)

    resting_endpoints = list(task_endpoints)

    # start cells are chosen from endpoints
    # deterministic because rng is seeded by the model
    start_cells = rng.sample(resting_endpoints, num_workers)

    return ProblemInstance(
        start_cells=start_cells,
        task_endpoints=task_endpoints,
        resting_endpoints=resting_endpoints,
        blocked_cells=blocked_cells,
    )

def build_random_scenario(
    grid,
    rng,
    num_workers,
    num_task_endpoints,
    blocked_spawn_probability,
):
    start_cells = generate_random_cells(
        grid=grid,
        rng=rng,
        count=num_workers,
    )

    task_endpoints = generate_random_cells(
        grid=grid,
        rng=rng,
        count=num_task_endpoints,
        forbidden=set(start_cells),
    )

    resting_endpoints = generate_random_cells(
        grid=grid,
        rng=rng,
        count=num_workers,
        forbidden=set(start_cells) | set(task_endpoints),
    )

    forbidden = set(start_cells) | set(task_endpoints) | set(resting_endpoints)

    blocked_cells = generate_valid_blocked_cells(
        grid=grid,
        rng=rng,
        blocked_spawn_probability=blocked_spawn_probability,
        forbidden=forbidden,
        important_cells=forbidden,
    )

    return ProblemInstance(
        start_cells=start_cells,
        task_endpoints=task_endpoints,
        resting_endpoints=resting_endpoints,
        blocked_cells=blocked_cells,
    )


def generate_random_cells(grid, rng, count, forbidden=None):
    forbidden = forbidden or set()

    available_cells = [
        cell for cell in grid.all_cells
        if cell not in forbidden
    ]

    if count > len(available_cells):
        raise ValueError("Not enough available cells to sample from")

    return rng.sample(available_cells, count)


def generate_valid_blocked_cells(
    grid,
    rng,
    blocked_spawn_probability,
    forbidden,
    important_cells,
    max_attempts=100,
):
    for _ in range(max_attempts):
        blocked_cells = generate_blocked_cells(
            grid=grid,
            rng=rng,
            blocked_spawn_probability=blocked_spawn_probability,
            forbidden=forbidden,
        )

        if is_connected_for_problem(
            important_cells=important_cells,
            blocked_cells=blocked_cells,
        ):
            return blocked_cells

    raise RuntimeError(
        "Could not generate a connected obstacle layout. "
        "Try reducing blocked_spawn_probability."
    )


def generate_blocked_cells(grid, rng, blocked_spawn_probability, forbidden):
    blocked_cells = set()

    for cell in grid.all_cells:
        if cell in forbidden:
            continue

        if rng.random() < blocked_spawn_probability:
            blocked_cells.add(cell)

    return blocked_cells


def is_connected_for_problem(important_cells, blocked_cells):
    if not important_cells:
        return True

    first_cell = next(iter(important_cells))
    reachable_cells = get_reachable_cells(first_cell, blocked_cells)

    return important_cells.issubset(reachable_cells)


def get_reachable_cells(start_cell, blocked_cells):
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


def remove_duplicates(cells):
    seen = set()
    result = []

    for cell in cells:
        if cell in seen:
            continue

        seen.add(cell)
        result.append(cell)

    return result