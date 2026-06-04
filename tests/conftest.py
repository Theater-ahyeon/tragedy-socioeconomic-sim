"""Shared fixtures for Tragedy test suite."""

import numpy as np
import pytest

from tragedy.core.agent import Agent, AgentSet
from tragedy.core.engine import SimulationEngine
from tragedy.core.random import RNGManager
from tragedy.models.yard_sale import YardSaleModel


@pytest.fixture
def rng_manager():
    """Create an RNG manager with a fixed seed."""
    return RNGManager(master_seed=42)


@pytest.fixture
def empty_engine():
    """Create an empty SimulationEngine."""
    return SimulationEngine(seed=42)


@pytest.fixture
def yard_sale_engine():
    """Create an engine with a Yard-Sale model set up (100 agents)."""
    engine = SimulationEngine(seed=42)
    model = YardSaleModel(num_agents=100, initial_wealth=100.0, collect_every=1)
    model.setup(engine)
    return engine, model


@pytest.fixture
def sample_agents():
    """Create a small AgentSet with test agents."""
    agents = AgentSet()
    for i in range(10):
        agent = Agent(agent_id=i, agent_type="TestAgent")
        agent.attributes["wealth"] = 100.0
        agents.add(agent)
    return agents


@pytest.fixture
def equal_wealth_array():
    """Return a numpy array with equal wealth values (Gini = 0)."""
    return np.ones(1000, dtype=np.float64) * 100.0


@pytest.fixture
def extreme_wealth_array():
    """Return a numpy array with extreme inequality (Gini ≈ 1)."""
    wealth = np.ones(1000, dtype=np.float64) * 0.01
    wealth[0] = 10000.0
    return wealth


@pytest.fixture
def random_wealth_array():
    """Return a numpy array with log-normal wealth distribution."""
    rng = np.random.default_rng(42)
    return rng.lognormal(mean=4.0, sigma=1.5, size=1000)
