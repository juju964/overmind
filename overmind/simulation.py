from __future__ import annotations

from collections import defaultdict


def pagerank(graph: dict[str, list[str]], iterations: int = 20, damping: float = 0.85) -> dict[str, float]:
    if not graph:
        return {}
    nodes = list(graph.keys())
    n = len(nodes)
    rank = {node: 1.0 / n for node in nodes}

    inbound: dict[str, list[str]] = defaultdict(list)
    out_degree = {node: len(targets) or 1 for node, targets in graph.items()}
    for src, targets in graph.items():
        for dst in targets:
            if dst in graph:
                inbound[dst].append(src)

    for _ in range(iterations):
        next_rank = {}
        for node in nodes:
            contribution = sum(rank[src] / out_degree[src] for src in inbound[node])
            next_rank[node] = (1 - damping) / n + damping * contribution
        rank = next_rank

    total = sum(rank.values()) or 1.0
    return {node: value / total for node, value in rank.items()}
