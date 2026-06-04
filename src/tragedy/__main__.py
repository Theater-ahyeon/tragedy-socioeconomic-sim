"""CLI entry point for running simulations without the web server.

Usage:
    python -m tragedy --model yard_sale --agents 1000 --ticks 5000
    python -m tragedy --model yard_sale --config configs/yard_sale.yaml --ticks 10000
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

import numpy as np

from tragedy.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tragedy — Agent-Based Socio-Economic Simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m tragedy --model yard_sale --agents 1000 --ticks 5000
  python -m tragedy --model yard_sale --config yard_sale.yaml --ticks 10000 --output results.csv
        """,
    )
    parser.add_argument("--model", type=str, default="yard_sale", help="Model name")
    parser.add_argument("--agents", type=int, default=1000, help="Number of agents")
    parser.add_argument("--ticks", type=int, default=5000, help="Number of ticks to run")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--config", type=str, default=None, help="Config file path")
    parser.add_argument("--collect-every", type=int, default=10, help="Collect metrics every N ticks")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    parser.add_argument("--log-level", type=str, default="INFO", help="Log level")
    args = parser.parse_args()

    setup_logging(level=args.log_level, fmt="console")

    # Import model
    if args.model == "yard_sale":
        from tragedy.models.yard_sale import YardSaleModel
        from tragedy.core.engine import SimulationEngine

        engine = SimulationEngine(seed=args.seed)

        # Load config if provided
        params = {
            "num_agents": args.agents,
            "seed": args.seed,
            "collect_every": args.collect_every,
        }
        if args.config:
            from tragedy.utils.config import config_to_model_params, load_config
            config = load_config(args.config)
            params.update(config_to_model_params(config))
        else:
            params["num_agents"] = args.agents

        model = YardSaleModel(**params)
        model.setup(engine)
    else:
        print(f"Unknown model: {args.model}", file=sys.stderr)
        sys.exit(1)

    # Run
    print(f"Running {args.model} with {len(engine.agents)} agents for {args.ticks} ticks...")
    start = time.perf_counter()

    try:
        engine.run(ticks=args.ticks)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        elapsed = time.perf_counter() - start
        ticks_run = engine.tick

    # Report
    wealth = np.array(engine.get_all_agent_attributes("wealth"), dtype=np.float64)
    from tragedy.metrics.inequality import gini_coefficient, pareto_alpha, wealth_deciles

    gini = gini_coefficient(wealth)
    alpha = pareto_alpha(wealth)
    deciles = wealth_deciles(wealth)

    print(f"\n{'='*50}")
    print(f"Simulation Complete")
    print(f"{'='*50}")
    print(f"Ticks:     {ticks_run}")
    print(f"Agents:    {len(engine.agents)}")
    print(f"Time:      {elapsed:.2f}s ({ticks_run/elapsed:.0f} ticks/s)")
    print(f"Total W:   ${np.sum(wealth):,.2f}")
    print(f"Mean W:    ${np.mean(wealth):,.2f}")
    print(f"Median W:  ${np.median(wealth):,.2f}")
    print(f"Min W:     ${np.min(wealth):,.4f}")
    print(f"Max W:     ${np.max(wealth):,.2f}")
    print(f"Gini:      {gini:.4f}")
    print(f"Pareto α:  {alpha:.2f}" if not np.isnan(alpha) else "Pareto α:  N/A")
    if deciles:
        print(f"Top 1%:    {deciles.get('top_1_pct_share', 0)*100:.1f}%")
        print(f"Top 10%:   {deciles.get('top_10_pct_share', 0)*100:.1f}%")
        print(f"Bottom 50%:{deciles.get('bottom_50_pct_share', 0)*100:.1f}%")

    # Export CSV if requested
    if args.output:
        import pandas as pd
        data = {
            "agent_id": [a.id for a in engine.agents],
            "wealth": wealth,
        }
        df = pd.DataFrame(data)
        df.to_csv(args.output, index=False)
        print(f"\nExported to: {args.output}")


if __name__ == "__main__":
    main()
