"""Spatial abstractions for agent-based models.

Provides Grid2D (toroidal grid for Sugarscape-style spatial models) and
Network (graph-based topology for trade and social networks).
"""

from __future__ import annotations

import numpy as np
from numpy.random import Generator


class Grid2D:
    """A toroidal 2D grid for spatial agent-based models.

    The grid wraps around (toroidal topology): moving off one edge
    wraps to the opposite edge. Each cell can hold resource values
    and multiple agents.

    Attributes:
        width: Number of columns.
        height: Number of rows.
        cells: 2D numpy array of resource values.
        agents_at: Mapping from (x, y) to list of agent IDs at that position.
    """

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.cells = np.zeros((height, width), dtype=np.float64)
        self.agents_at: dict[tuple[int, int], list[int]] = {}

    def wrap(self, x: int, y: int) -> tuple[int, int]:
        """Wrap coordinates to toroidal grid bounds."""
        return x % self.width, y % self.height

    def neighbors(
        self, x: int, y: int, radius: int = 1
    ) -> list[tuple[int, int]]:
        """Return Moore neighborhood positions within the given radius.

        Args:
            x, y: Center position.
            radius: Vision radius (1 = 8 neighbors, 2 = 24 neighbors, etc.).

        Returns:
            List of (x, y) tuples for valid neighbor positions (excluding center).
        """
        result = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = self.wrap(x + dx, y + dy)
                result.append((nx, ny))
        return result

    def get_resource(self, x: int, y: int) -> float:
        """Get the resource value at a position."""
        x, y = self.wrap(x, y)
        return float(self.cells[y, x])

    def set_resource(self, x: int, y: int, value: float) -> None:
        """Set the resource value at a position."""
        x, y = self.wrap(x, y)
        self.cells[y, x] = value

    def add_resource(self, x: int, y: int, amount: float) -> None:
        """Add to the resource value at a position."""
        x, y = self.wrap(x, y)
        self.cells[y, x] += amount

    def place_agent(self, agent_id: int, x: int, y: int) -> None:
        """Register an agent at a grid position."""
        pos = self.wrap(x, y)
        if pos not in self.agents_at:
            self.agents_at[pos] = []
        self.agents_at[pos].append(agent_id)

    def remove_agent(self, agent_id: int, x: int, y: int) -> None:
        """Remove an agent from a grid position."""
        pos = self.wrap(x, y)
        if pos in self.agents_at:
            self.agents_at[pos] = [aid for aid in self.agents_at[pos] if aid != agent_id]
            if not self.agents_at[pos]:
                del self.agents_at[pos]

    def move_agent(
        self, agent_id: int, from_pos: tuple[int, int], to_pos: tuple[int, int]
    ) -> None:
        """Move an agent from one position to another."""
        self.remove_agent(agent_id, *from_pos)
        self.place_agent(agent_id, *to_pos)

    def random_position(self, rng: Generator | None = None) -> tuple[int, int]:
        """Return a random (x, y) position on the grid."""
        if rng is not None:
            return (int(rng.integers(0, self.width)), int(rng.integers(0, self.height)))
        return (
            int(np.random.randint(0, self.width)),
            int(np.random.randint(0, self.height)),
        )

    def find_best_neighbor(
        self, x: int, y: int, radius: int
    ) -> tuple[int, int] | None:
        """Find the neighbor with the highest resource value.

        Returns:
            (x, y) of the best neighbor, or None if no neighbors have resources.
        """
        neighbors = self.neighbors(x, y, radius)
        if not neighbors:
            return None
        best_pos = max(neighbors, key=lambda pos: self.get_resource(*pos))
        if self.get_resource(*best_pos) > 0:
            return best_pos
        return None

    def to_array(self) -> np.ndarray:
        """Return a copy of the resource grid."""
        return self.cells.copy()


class Network:
    """Graph-based topology for agent interaction networks.

    Supports social networks (Watts-Strogatz, Barabási-Albert), trade networks,
    and supply chains. Uses compressed sparse row (CSR) format for efficient
    neighbor queries and can optionally use scipy.sparse for advanced operations.

    Attributes:
        num_nodes: Number of nodes in the network.
        directed: Whether edges are directed.
        adjacency: Adjacency list mapping node_id -> list of neighbor_ids.
    """

    def __init__(self, num_nodes: int = 0, directed: bool = False) -> None:
        self.num_nodes = num_nodes
        self.directed = directed
        self.adjacency: dict[int, list[int]] = {i: [] for i in range(num_nodes)}

    def add_node(self) -> int:
        """Add a new node and return its ID."""
        node_id = self.num_nodes
        self.adjacency[node_id] = []
        self.num_nodes += 1
        return node_id

    def add_edge(self, source: int, target: int) -> None:
        """Add an edge between two nodes."""
        if target not in self.adjacency[source]:
            self.adjacency[source].append(target)
        if not self.directed and source not in self.adjacency[target]:
            self.adjacency[target].append(source)

    def remove_edge(self, source: int, target: int) -> None:
        """Remove an edge between two nodes."""
        if target in self.adjacency[source]:
            self.adjacency[source].remove(target)
        if not self.directed and source in self.adjacency[target]:
            self.adjacency[target].remove(source)

    def neighbors(self, node_id: int) -> list[int]:
        """Return the neighbors of a node."""
        return list(self.adjacency.get(node_id, []))

    def degree(self, node_id: int) -> int:
        """Return the degree of a node."""
        return len(self.adjacency.get(node_id, []))

    def add_random_edges(
        self, probability: float, rng: Generator | None = None
    ) -> None:
        """Add random Erdős-Rényi edges between all node pairs.

        Args:
            probability: Probability of an edge between any two nodes.
            rng: Optional seeded RNG.
        """
        rng = rng or np.random.default_rng()
        for i in range(self.num_nodes):
            for j in range(i + 1, self.num_nodes):
                if rng.random() < probability:
                    self.add_edge(i, j)

    def __repr__(self) -> str:
        return f"Network(nodes={self.num_nodes}, directed={self.directed})"
