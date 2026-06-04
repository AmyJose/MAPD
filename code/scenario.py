from problem_instance import ProblemInstance

def build_scenario(
        name,
        grid,
        rng,
        num_workers=3,
        num_task_endpoints=8,
        blocked_spawn_probability=0.15,
    ):

    if name == "test":
        problem= build_test_scenario(grid, rng)
    
    elif name == "warehouse":
        problem= build_warehouse_scenario(grid, rng)
    
    elif name == "random":
        problem= build_random_scenario(
            grid=grid,
            rng=rng,
            num_workers=num_workers,
            num_task_endpoints=num_task_endpoints,
            blocked_spawn_probability=blocked_spawn_probability,
        )
    
    else : 
        raise ValueError(f"Unknown scenario: {name}")

    validate_problem_instance(problem, num_workers=len(problem.start_cells))

    return problem


def build_test_scenario(grid, rng, num_workers=2):
    blocked_cells = set()

    task_endpoints = [
        grid[(0, 1)],
        grid[(4, 1)],
    ]

    resting_endpoints = [
        grid[(1, 1)],
        grid[(2, 0)],
        grid[(2, 2)],
        grid[(3, 1)],
    ]

    if num_workers > len(resting_endpoints):
        raise ValueError(
            f"Test scenario only has {len(resting_endpoints)} resting endpoints, "
            f"but {num_workers} workers were requested."
        )

    start_cells = resting_endpoints[:num_workers]

    return ProblemInstance(
        start_cells=start_cells,
        task_endpoints=task_endpoints,
        resting_endpoints=resting_endpoints,
        blocked_cells=blocked_cells,
    )

def build_warehouse_scenario(grid, rng):
    num_workers = 50

    task_endpoints = []
    blocked_cells = set()

    shelf_y_values = [2, 6, 10, 14, 18]

    for y in shelf_y_values:
        #finishes at 16
        for x in range(7, 17):
            blocked_cells.add(grid[(x, y)])

        for x in range(18, 28):
            blocked_cells.add(grid[(x, y)])

    side_endpoint_columns = [1, 2, 4, 5, 29, 30, 32, 33]

    for x in side_endpoint_columns:
        for y in range(1, 20):
            cell = grid[(x, y)]

            if cell not in blocked_cells:
                task_endpoints.append(cell)

    # all shelf adjacent cells -> task endpoits
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

    possible_start_cells = []

    for x in side_endpoint_columns:
        for y in range(1, 20):
            cell = grid[(x, y)]

            if cell not in blocked_cells:
                possible_start_cells.append(cell)

    possible_start_cells = remove_duplicates(possible_start_cells)

    start_cells = rng.sample(possible_start_cells, num_workers)

    #cells where agentrs tart become non task endpoints
    start_cell_set = set(start_cells)

    task_endpoints = [
        cell
        for cell in task_endpoints
        if cell not in start_cell_set
    ]

    resting_endpoints = start_cells

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
    resting_endpoints = generate_random_cells(
        grid=grid,
        rng=rng,
        count=num_workers,
    )

    start_cells = list(resting_endpoints)

    task_endpoints = generate_random_cells(
        grid=grid,
        rng=rng,
        count=num_task_endpoints,
        forbidden=set(resting_endpoints),
    )

    endpoints = set(resting_endpoints) | set(task_endpoints)

    blocked_cells = generate_valid_blocked_cells(
        grid=grid,
        rng=rng,
        blocked_spawn_probability=blocked_spawn_probability,
        forbidden=endpoints,
        important_cells=endpoints,
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

def validate_problem_instance(problem, num_workers):
    task_endpoints = set(problem.task_endpoints)
    resting_endpoints = set(problem.resting_endpoints)
    start_cells = set(problem.start_cells)
    blocked_cells = set(problem.blocked_cells)
    endpoints = set(problem.endpoints)

    if len(problem.start_cells) != num_workers:
        raise ValueError(
            f"Expected {num_workers} start cells, got {len(problem.start_cells)}."
        )

    if len(start_cells) != len(problem.start_cells):
        raise ValueError("Start cells must be unique.")

    if not start_cells.issubset(resting_endpoints):
        raise ValueError("All start cells must also be resting endpoints.")

    if not task_endpoints.isdisjoint(resting_endpoints):
        overlap = task_endpoints & resting_endpoints
        raise ValueError(
            f"Task endpoints and resting endpoints must be disjoint. "
            f"Overlap: {[cell.coordinate for cell in overlap]}"
        )

    if blocked_cells & task_endpoints:
        raise ValueError("Blocked cells cannot also be task endpoints.")

    if blocked_cells & resting_endpoints:
        raise ValueError("Blocked cells cannot also be resting endpoints.")

    if blocked_cells & start_cells:
        raise ValueError("Blocked cells cannot also be start cells.")

    if len(task_endpoints) < 2:
        raise ValueError("At least two task endpoints are required.")

    if len(resting_endpoints) < num_workers:
        raise ValueError(
            f"Need at least {num_workers} resting endpoints, "
            f"got {len(resting_endpoints)}."
        )

    if endpoints != task_endpoints | resting_endpoints:
        raise ValueError(
            "problem.endpoints must equal task_endpoints + resting_endpoints."
        )