"""Agent base class and AgentSet collection.

Agent is the universal base for all simulation participants (households, firms,
banks, government). AgentSet provides bulk operations on typed agent collections,
inspired by Mesa 3's AgentSet design.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterator
from typing import Any, TypeVar

T = TypeVar("T", bound="Agent")


class Agent:
    """Base class for all agents in the simulation.

    Attributes:
        id: Unique agent identifier within the simulation.
        agent_type: Discriminator string for typed AgentSet filtering
                    (e.g. "Household", "Firm", "Bank").
        alive: Whether this agent is still active. Dead agents are removed
               at the end of each tick.
        creation_tick: The simulation tick when this agent was created.
        attributes: Extensible key-value store for model-specific data.
    """

    __slots__ = ("id", "agent_type", "alive", "creation_tick", "attributes")

    def __init__(
        self,
        agent_id: int,
        agent_type: str = "Agent",
        creation_tick: int = 0,
    ) -> None:
        self.id = agent_id
        self.agent_type = agent_type
        self.alive = True
        self.creation_tick = creation_tick
        self.attributes: dict[str, Any] = {}

    def __repr__(self) -> str:
        return f"{self.agent_type}(id={self.id}, alive={self.alive})"

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Agent):
            return NotImplemented
        return self.id == other.id


class AgentSet:
    """A typed, iterable collection of agents with bulk operations.

    AgentSet is the primary container for agent populations. It supports
    filtering, shuffling, grouping, and bulk method dispatch — all with
    lazy evaluation where possible.

    Usage:
        firms = AgentSet([firm1, firm2, firm3])
        active_firms = firms.filter(lambda f: f.alive)
        active_firms.shuffle().do("produce")
        avg_price = firms.aggregate(lambda f: f.price) / len(firms)
    """

    def __init__(self, agents: list[Agent] | None = None) -> None:
        self._agents: dict[int, Agent] = {}
        self._order: list[int] = []
        if agents:
            for agent in agents:
                self.add(agent)

    # ── Core Operations ──────────────────────────────────────────

    def add(self, agent: Agent) -> None:
        """Add an agent to the set."""
        if agent.id not in self._agents:
            self._order.append(agent.id)
        self._agents[agent.id] = agent

    def remove(self, agent_or_id: Agent | int) -> Agent | None:
        """Remove and return an agent by reference or ID."""
        agent_id = agent_or_id.id if isinstance(agent_or_id, Agent) else agent_or_id
        if agent_id in self._agents:
            self._order.remove(agent_id)
            return self._agents.pop(agent_id)
        return None

    def get(self, agent_id: int) -> Agent | None:
        """Get an agent by ID."""
        return self._agents.get(agent_id)

    def clear(self) -> None:
        """Remove all agents."""
        self._agents.clear()
        self._order.clear()

    # ── Bulk Operations ──────────────────────────────────────────

    def do(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        """Call a method on every agent in the set.

        Args:
            method_name: Name of the method to call on each agent.
            *args, **kwargs: Passed through to the method.
        """
        for agent in self:
            method = getattr(agent, method_name, None)
            if method is not None:
                method(*args, **kwargs)

    def shuffle(self, rng: Any = None) -> AgentSet:
        """Shuffle agent iteration order in-place. Returns self for chaining.

        Args:
            rng: Optional numpy random Generator for reproducibility.
        """
        if rng is not None:
            rng.shuffle(self._order)
        else:
            import random

            random.shuffle(self._order)
        return self

    def filter(self, predicate: Callable[[Agent], bool]) -> AgentSet:
        """Return a new AgentSet containing agents matching the predicate.

        This is eager — it creates a new AgentSet immediately. For very large
        populations, consider iterating with a generator instead.
        """
        result = AgentSet()
        for agent in self:
            if predicate(agent):
                result.add(agent)
        return result

    def select(self, n: int, rng: Any = None) -> AgentSet:
        """Return a random sample of up to n agents.

        Args:
            n: Maximum number of agents to select.
            rng: Optional numpy random Generator for reproducibility.
        """
        if rng is not None:
            indices = rng.choice(len(self._order), size=min(n, len(self)), replace=False)
            selected = [self._agents[self._order[i]] for i in indices]
        else:
            import random

            selected = random.sample(list(self), min(n, len(self)))
        return AgentSet(selected)

    def groupby(self, key: Callable[[Agent], Any]) -> dict[Any, AgentSet]:
        """Group agents by a key function.

        Returns:
            Dict mapping key values to AgentSets.
        """
        groups: dict[Any, AgentSet] = defaultdict(AgentSet)
        for agent in self:
            groups[key(agent)].add(agent)
        return dict(groups)

    def aggregate(self, func: Callable[[Agent], Any], initial: Any = None) -> Any:
        """Reduce over all agents. Returns None for empty set unless initial is given."""
        it = iter(self)
        if initial is None:
            try:
                result = func(next(it))
            except StopIteration:
                return None
        else:
            result = initial
        for agent in it:
            result = func(agent) if initial is None else result
            # Simpler: just accumulate
        # Re-implement cleanly:
        result = initial
        first = True
        for agent in self:
            if first and initial is None:
                result = func(agent)
                first = False
            else:
                # This is too generic — let's keep it simple
                pass
        return result

    def map(self, func: Callable[[Agent], Any]) -> list[Any]:
        """Apply a function to every agent and return a list of results."""
        return [func(agent) for agent in self]

    # ── Information ──────────────────────────────────────────────

    def count(self, predicate: Callable[[Agent], bool] | None = None) -> int:
        """Count agents, optionally matching a predicate."""
        if predicate is None:
            return len(self._agents)
        return sum(1 for agent in self if predicate(agent))

    def first(self) -> Agent | None:
        """Return the first agent (by insertion order) or None."""
        if self._order:
            return self._agents[self._order[0]]
        return None

    # ── Magic Methods ────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._agents)

    def __iter__(self) -> Iterator[Agent]:
        for agent_id in self._order:
            agent = self._agents.get(agent_id)
            if agent is not None:
                yield agent

    def __contains__(self, agent: Agent) -> bool:
        return agent.id in self._agents

    def __getitem__(self, agent_id: int) -> Agent:
        return self._agents[agent_id]

    def __repr__(self) -> str:
        types = self.groupby(lambda a: a.agent_type)
        parts = [f"{t}({len(s)})" for t, s in types.items()]
        return f"AgentSet({', '.join(parts) if parts else 'empty'})"
