"""Seeded RNG manager for reproducible stochasticity.

Every agent gets a deterministic random sub-stream derived from the master seed
via numpy's SeedSequence. This ensures that:
1. Same master seed → identical simulation results, regardless of agent
   activation order or parallel execution strategy.
2. Adding/removing agents doesn't change existing agents' random sequences
   (each agent's stream is independent).
3. A/B testing of model parameters is free of RNG noise.
"""

from __future__ import annotations

import numpy as np
from numpy.random import Generator, PCG64, SeedSequence


class RNGManager:
    """Manages seeded random number generators for reproducible simulations.

    Usage:
        rng = RNGManager(master_seed=42)
        agent_rng = rng.agent_rng(agent_id=7)
        value = agent_rng.random()  # Deterministic for agent 7 with seed 42
    """

    def __init__(self, master_seed: int = 42) -> None:
        self.master_seed = master_seed
        self._master_sequence = SeedSequence(master_seed)
        self._master_rng = Generator(PCG64(self._master_sequence))
        self._child_sequences: dict[int, SeedSequence] = {}

    @property
    def master_rng(self) -> Generator:
        """The master RNG, used for non-agent-specific randomness."""
        return self._master_rng

    def agent_rng(self, agent_id: int) -> Generator:
        """Get a deterministic RNG substream for a specific agent.

        Each agent gets its own independent random stream. The same agent_id
        always yields the same sequence for a given master seed.
        """
        if agent_id not in self._child_sequences:
            # Spawn a child sequence for this agent
            child_seeds = self._master_sequence.spawn(1)
            self._child_sequences[agent_id] = child_seeds[0]
        return Generator(PCG64(self._child_sequences[agent_id]))

    def market_rng(self, market_name: str) -> Generator:
        """Get a deterministic RNG substream for a market mechanism.

        Uses a hash of the market name to create a stable substream.
        """
        name_hash = hash(market_name) & 0x7FFFFFFF
        child_seq = SeedSequence([self.master_seed, name_hash])
        return Generator(PCG64(child_seq))

    def reset(self) -> None:
        """Reset all child sequences. Next agent_rng() calls will recreate them."""
        self._child_sequences.clear()
        self._master_sequence = SeedSequence(self.master_seed)
        self._master_rng = Generator(PCG64(self._master_sequence))
