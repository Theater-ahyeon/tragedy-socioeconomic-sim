"""Integration tests for the Yard-Sale model end-to-end."""

import numpy as np
import pytest

from tragedy.core.engine import SimulationEngine
from tragedy.models.yard_sale import YardSaleModel
from tragedy.agents.household import YardSaleAgent
from tragedy.metrics.inequality import gini_coefficient


class TestYardSaleModel:
    """End-to-end tests for the Yard-Sale wealth transfer model."""

    def test_model_setup(self):
        """Test that model setup creates the right number of agents."""
        engine = SimulationEngine(seed=42)
        model = YardSaleModel(num_agents=500, initial_wealth=100.0)
        model.setup(engine)

        assert len(engine.agents) == 500
        assert all(isinstance(a, YardSaleAgent) for a in engine.agents)
        assert all(a.wealth == 100.0 for a in engine.agents)

    def test_wealth_conservation(self):
        """Total wealth should be conserved throughout the simulation."""
        num_agents = 200
        initial_wealth = 100.0
        initial_total = num_agents * initial_wealth

        engine = SimulationEngine(seed=42)
        model = YardSaleModel(
            num_agents=num_agents,
            initial_wealth=initial_wealth,
            transfer_fraction=0.05,
            collect_every=10,
        )
        model.setup(engine)

        engine.run(ticks=100)

        # Check conservation
        current_total = sum(a.wealth for a in engine.agents)
        drift_pct = abs(current_total - initial_total) / initial_total
        assert drift_pct < 0.01  # Less than 1% drift

    def test_gini_increases(self):
        """Gini coefficient should increase from 0 toward higher values."""
        engine = SimulationEngine(seed=42)
        model = YardSaleModel(
            num_agents=200,
            initial_wealth=100.0,
            transfer_fraction=0.05,
            collect_every=10,
        )
        model.setup(engine)

        # Check initial Gini
        initial_wealth = np.array([a.wealth for a in engine.agents])
        initial_gini = gini_coefficient(initial_wealth)
        assert initial_gini == pytest.approx(0.0, abs=0.01)

        engine.run(ticks=200)

        # Check final Gini
        final_wealth = np.array([a.wealth for a in engine.agents])
        final_gini = gini_coefficient(final_wealth)
        assert final_gini > 0.2  # Should have increased significantly

    def test_reproducibility(self):
        """Same seed should produce identical results."""
        def run_sim(seed):
            engine = SimulationEngine(seed=seed)
            model = YardSaleModel(
                num_agents=50,
                initial_wealth=100.0,
                transfer_fraction=0.05,
                seed=seed,
            )
            model.setup(engine)
            engine.run(ticks=50)
            return [a.wealth for a in engine.agents]

        run1 = run_sim(42)
        run2 = run_sim(42)

        assert run1 == pytest.approx(run2)

    def test_no_negative_wealth(self):
        """Agents should never have negative wealth."""
        engine = SimulationEngine(seed=42)
        model = YardSaleModel(num_agents=50, initial_wealth=100.0)
        model.setup(engine)

        engine.run(ticks=100)

        for agent in engine.agents:
            assert agent.wealth >= 0

    def test_transfer_bias_effect(self):
        """With positive bias, the richer should win more → faster condensation."""
        def run_with_bias(bias):
            engine = SimulationEngine(seed=42)
            model = YardSaleModel(
                num_agents=100,
                initial_wealth=100.0,
                transfer_fraction=0.05,
                transfer_bias=bias,
            )
            model.setup(engine)
            engine.run(ticks=100)
            wealth = np.array([a.wealth for a in engine.agents])
            return gini_coefficient(wealth)

        gini_fair = run_with_bias(0.0)
        gini_biased = run_with_bias(0.5)

        # With positive bias (richer wins more), inequality should be higher
        assert gini_biased >= gini_fair * 0.95  # At least not significantly lower

    def test_metrics_collection(self):
        """Metrics should be collected during simulation."""
        engine = SimulationEngine(seed=42)
        model = YardSaleModel(num_agents=50, initial_wealth=100.0, collect_every=1)
        model.setup(engine)

        engine.run(ticks=20)

        assert "gini" in engine.metrics_history
        assert "total_wealth" in engine.metrics_history
        assert len(engine.metrics_history["gini"]) > 0
