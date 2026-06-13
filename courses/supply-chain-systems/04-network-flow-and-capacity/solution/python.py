"""Find the maximum weekly flow through a small supply network."""

from collections import deque


def add_edge(graph, u, v, capacity):
    graph.setdefault(u, {})[v] = graph.setdefault(u, {}).get(v, 0) + capacity
    graph.setdefault(v, {})


def bfs(residual, source, sink):
    parent = {source: None}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v, capacity in residual[u].items():
            if capacity > 0 and v not in parent:
                parent[v] = u
                if v == sink:
                    return parent
                queue.append(v)
    return None


def max_flow(capacity, source, sink):
    residual = {u: dict(edges) for u, edges in capacity.items()}
    for u, edges in list(capacity.items()):
        for v in edges:
            residual.setdefault(v, {})
            residual[v].setdefault(u, 0)

    total = 0
    while True:
        parent = bfs(residual, source, sink)
        if parent is None:
            break

        increment = float("inf")
        v = sink
        while v != source:
            u = parent[v]
            increment = min(increment, residual[u][v])
            v = u

        v = sink
        while v != source:
            u = parent[v]
            residual[u][v] -= increment
            residual[v][u] += increment
            v = u

        total += increment

    return total, residual


def shipped_on(capacity, residual, u, v):
    return capacity[u][v] - residual[u][v]


def build_network():
    graph = {}
    for edge in [
        ("source", "supplier_a", 40),
        ("source", "supplier_b", 30),
        ("supplier_a", "plant_1", 25),
        ("supplier_a", "plant_2", 20),
        ("supplier_b", "plant_1", 15),
        ("supplier_b", "plant_2", 25),
        ("plant_1", "warehouse", 30),
        ("plant_1", "demand", 10),
        ("plant_2", "warehouse", 20),
        ("plant_2", "demand", 15),
        ("warehouse", "demand", 35),
    ]:
        add_edge(graph, *edge)
    return graph


def main():
    capacity = build_network()
    total, residual = max_flow(capacity, "source", "demand")

    print(f"maximum customer flow: {total}")
    for u, v in [
        ("source", "supplier_a"),
        ("source", "supplier_b"),
        ("plant_1", "warehouse"),
        ("plant_2", "warehouse"),
        ("warehouse", "demand"),
    ]:
        print(f"{u}->{v}: {shipped_on(capacity, residual, u, v)}")


if __name__ == "__main__":
    main()
