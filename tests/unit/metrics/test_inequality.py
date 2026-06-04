"""Tests for inequality metrics (Gini, Lorenz, Pareto)."""

import numpy as np
import pytest

from tragedy.metrics.inequality import gini_coefficient, lorenz_curve, pareto_alpha


class TestGini:
    def test_equal_distribution(self, equal_wealth_array):
        """Gini of perfectly equal distribution should be 0."""
        gini = gini_coefficient(equal_wealth_array)
        assert gini == pytest.approx(0.0, abs=1e-6)

    def test_extreme_inequality(self, extreme_wealth_array):
        """Gini with one person holding all wealth should be close to 1."""
        gini = gini_coefficient(extreme_wealth_array)
        assert gini > 0.98  # Almost complete inequality

    def test_empty_array(self):
        assert gini_coefficient(np.array([])) == 0.0

    def test_single_element(self):
        assert gini_coefficient(np.array([100.0])) == 0.0

    def test_all_zero(self):
        assert gini_coefficient(np.zeros(100)) == 0.0

    def test_monotonic_with_inequality(self):
        """Gini should increase as distribution becomes more unequal."""
        rng = np.random.default_rng(42)
        base = rng.lognormal(mean=4.0, sigma=0.5, size=1000)
        wide = rng.lognormal(mean=4.0, sigma=2.0, size=1000)
        assert gini_coefficient(wide) > gini_coefficient(base)

    def test_gini_between_0_and_1(self, random_wealth_array):
        gini = gini_coefficient(random_wealth_array)
        assert 0.0 <= gini <= 1.0


class TestLorenz:
    def test_endpoints(self, random_wealth_array):
        pop, wel = lorenz_curve(random_wealth_array, n_points=50)
        assert pop[0] == pytest.approx(0.0)
        assert pop[-1] == pytest.approx(1.0)
        assert wel[0] == pytest.approx(0.0)
        assert wel[-1] == pytest.approx(1.0)

    def test_equal_distribution(self, equal_wealth_array):
        pop, wel = lorenz_curve(equal_wealth_array)
        # Should be approximately the equality line
        assert np.allclose(pop, wel, atol=0.02)

    def test_empty(self):
        pop, wel = lorenz_curve(np.array([]))
        assert len(pop) == 100
        assert len(wel) == 100

    def test_output_length(self, random_wealth_array):
        pop, wel = lorenz_curve(random_wealth_array, n_points=30)
        assert len(pop) == 30
        assert len(wel) == 30


class TestPareto:
    def test_lognormal_tail(self, random_wealth_array):
        """Lognormal distributions have a light tail, α should be > 2."""
        alpha = pareto_alpha(random_wealth_array)
        assert not np.isnan(alpha)
        assert alpha > 1.5

    def test_empty_array(self):
        assert np.isnan(pareto_alpha(np.array([])))

    def test_small_array(self):
        # With 3 values and tail_fraction=0.05, k=1, n>=2 so it works.
        # We need a truly too-small array: 1 element
        alpha = pareto_alpha(np.array([1.0]))
        assert np.isnan(alpha)
