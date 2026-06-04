"""Social network generators for agent-based economic simulations.

Provides generators for structured interaction topologies that replace
random global pairing with realistic network-constrained interaction.

Reference:
    Watts, D. J., & Strogatz, S. H. (1998). "Collective dynamics of
    'small-world' networks." Nature, 393(6684), 440-442.
"""

from __future__ import annotations

import numpy as np
from numpy.random import Generator

from tragedy.core.space import Network


def watts_strogatz_network(
    num_nodes: int,
    k: int = 4,
    p: float = 0.1,
    rng: Generator | None = None,
) -> Network:
    """Create a Watts-Strogatz small-world network.

    Starts with a ring lattice where each node connects to k/2 nearest
    neighbors on each side. Then rewires each edge with probability p,
    replacing the target with a random node (avoiding self-loops and
    duplicate edges).

    Args:
        num_nodes: Number of nodes (agents).
        k: Each node connected to k nearest neighbors (must be even, >= 2).
        p: Rewiring probability. p=0 = ring lattice, p=1 ≈ Erdős-Rényi.
        rng: Seeded random generator for reproducibility.

    Returns:
        A Network instance with the generated edges.

    Raises:
        ValueError: If k is odd or num_nodes < k + 1.
    """
    if k % 2 != 0:
        raise ValueError(f"k must be even, got {k}")
    if num_nodes < k + 1:
        raise ValueError(f"num_nodes ({num_nodes}) must be >= k+1 ({k+1})")

    if rng is None:
        rng = np.random.default_rng()

    net = Network(num_nodes=num_nodes, directed=False)

    half_k = k // 2

    # Step 1: Create ring lattice
    for i in range(num_nodes):
        for j in range(1, half_k + 1):
            target = (i + j) % num_nodes
            net.add_edge(i, target)

    # Step 2: Rewire edges
    for i in range(num_nodes):
        for j in range(1, half_k + 1):
            if rng.random() < p:
                # Pick a new target (not self, not already connected)
                current_target = (i + j) % num_nodes
                existing = set(net.neighbors(i))
                existing.add(i)  # Exclude self

                # Find a valid new target
                candidates = [n for n in range(num_nodes) if n not in existing]
                if candidates:
                    new_target = int(rng.choice(candidates))
                    net.remove_edge(i, current_target)
                    net.add_edge(i, new_target)

    return net


def barabasi_albert_network(
    num_nodes: int,
    m: int = 2,
    rng: Generator | None = None,
) -> Network:
    """Create a Barabási-Albert scale-free network via preferential attachment.

    Nodes are added one at a time, each connecting to m existing nodes
    with probability proportional to their current degree.

    Args:
        num_nodes: Total number of nodes.
        m: Number of edges per new node (must be >= 1).
        rng: Seeded random generator.

    Returns:
        A Network instance with power-law degree distribution.
    """
    if rng is None:
        rng = np.random.default_rng()

    net = Network(num_nodes=num_nodes, directed=False)

    if num_nodes <= m:
        # Fully connect all nodes
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                net.add_edge(i, j)
        return net

    # Start with a fully connected cluster of m nodes
    for i in range(m):
        for j in range(i + 1, m):
            net.add_edge(i, j)

    # Add remaining nodes with preferential attachment
    degrees = [net.degree(n) for n in range(num_nodes)]

    for new_node in range(m, num_nodes):
        total_degree = sum(degrees[:new_node])
        if total_degree == 0:
            # Connect randomly
            targets = list(rng.choice(new_node, size=min(m, new_node), replace=False))
        else:
            # Preferential attachment
            probabilities = [degrees[i] / total_degree for i in range(new_node)]
            targets = list(
                rng.choice(new_node, size=min(m, new_node), replace=False, p=probabilities)
            )

        for target in targets:
            net.add_edge(new_node, int(target))
            degrees[new_node] += 1
            degrees[int(target)] += 1

    return net


def compute_clustering_coefficient(net: Network) -> float:
    """Compute the average local clustering coefficient.

    For each node, clustering = (edges among neighbors) / (possible edges among neighbors).

    Args:
        net: The network to analyze.

    Returns:
        Mean clustering coefficient across all nodes with degree >= 2.
    """
    total = 0.0
    n_valid = 0

    for i in range(net.num_nodes):
        neighbors_i = set(net.neighbors(i))
        k_i = len(neighbors_i)
        if k_i < 2:
            continue

        edges_among = 0
        neighbor_list = list(neighbors_i)
        for a in range(len(neighbor_list)):
            for b in range(a + 1, len(neighbor_list)):
                if neighbor_list[b] in set(net.neighbors(neighbor_list[a])):
                    edges_among += 1

        possible = k_i * (k_i - 1) / 2
        total += edges_among / possible
        n_valid += 1

    return total / n_valid if n_valid > 0 else 0.0


def compute_degree_gini(net: Network) -> float:
    """Compute the Gini coefficient of the degree distribution.

    High values indicate that a few nodes are much more connected than others.

    Args:
        net: The network to analyze.

    Returns:
        Gini of degree distribution (0 = equal, 1 = one node has all edges).
    """
    degrees = np.array([net.degree(i) for i in range(net.num_nodes)], dtype=np.float64)
    if len(degrees) <= 1 or np.sum(degrees) == 0:
        return 0.0

    from tragedy.metrics.inequality import gini_coefficient

    return float(gini_coefficient(degrees))
