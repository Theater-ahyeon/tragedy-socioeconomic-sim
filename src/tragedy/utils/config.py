"""YAML configuration loader with schema validation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML configuration file.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed configuration dictionary.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        yaml.YAMLError: If the file is malformed.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if config is None:
        config = {}

    logger.debug("Loaded config from %s", path)
    return config


def merge_configs(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge two configuration dictionaries.

    Values from `override` take precedence over `base`. Nested
    dictionaries are merged recursively.

    Args:
        base: The base/default configuration.
        override: The overriding configuration.

    Returns:
        A new merged dictionary.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    return result


def config_to_model_params(config: dict[str, Any]) -> dict[str, Any]:
    """Extract model constructor parameters from a configuration dict.

    Args:
        config: Full configuration dictionary.

    Returns:
        Dict of parameters suitable for model class __init__.
    """
    model_section = config.get("model", {})
    agent_section = config.get("agents", {})
    transfer_section = config.get("transfer", {})
    sim_section = config.get("simulation", {})

    params = {}
    params["name"] = model_section.get("name", "yard_sale")
    params["seed"] = model_section.get("seed", 42)
    params["num_agents"] = agent_section.get("num_households", 1000)
    params["initial_wealth"] = agent_section.get("initial_wealth", 100.0)
    params["transfer_fraction"] = transfer_section.get("fraction", 0.05)
    params["transfer_bias"] = transfer_section.get("bias", 0.0)
    params["collect_every"] = sim_section.get("collect_every", 1)

    # Phase 1.5: Network interaction
    network_section = config.get("network", {})
    params["network_type"] = network_section.get("type", "random_global")
    params["ws_k"] = int(network_section.get("ws_k", 4))
    params["ws_p"] = float(network_section.get("ws_p", 0.1))
    params["trades_per_tick"] = int(network_section.get("trades_per_tick", 1))

    # Phase 1.5: Heterogeneous strategies
    strategy_section = config.get("strategy", {})
    params["heterogeneous_strategy"] = strategy_section.get("heterogeneous", True)
    params["savings_rate_mean"] = float(strategy_section.get("savings_rate_mean", 0.05))
    params["savings_rate_std"] = float(strategy_section.get("savings_rate_std", 0.02))
    params["risk_tolerance_mean"] = float(strategy_section.get("risk_tolerance_mean", 0.0))
    params["risk_tolerance_std"] = float(strategy_section.get("risk_tolerance_std", 0.05))

    # Phase 1.5: Imitation learning
    imitation_section = config.get("imitation", {})
    params["imitation_enabled"] = imitation_section.get("enabled", True)
    params["imitation_interval"] = int(imitation_section.get("interval", 20))
    params["imitation_probability"] = float(imitation_section.get("probability", 0.3))
    params["imitation_noise"] = float(imitation_section.get("noise", 0.01))

    return params
