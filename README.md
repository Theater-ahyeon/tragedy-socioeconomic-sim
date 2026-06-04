# 🏛️ Tragedy — Agent-Based Socio-Economic Simulation

**Tragedy** is a computational economics simulation system that models the emergence of macroeconomic patterns — inequality, business cycles, market dynamics — from the bottom-up interaction of heterogeneous agents.

Built on the academic foundations of **Agent-Based Computational Economics (ACE)**, it implements canonical models from the literature and provides real-time visualization of emergent economic phenomena.

## Academic Foundations

Tragedy draws on key models from the ACE literature:

| Model | Reference | Key Insight |
|-------|-----------|-------------|
| **Yard-Sale** | Yakovenko & Rosser (2009) | Multiplicative asymmetry in random transfers drives wealth condensation and Pareto power-law tails |
| **Sugarscape** | Epstein & Axtell (1996) | Heterogeneous agents with simple local rules generate emergent inequality, carrying-capacity dynamics, and decentralized price equilibria |
| **K+S Macro** | Dosi, Fagiolo & Roventini (2010) | Schumpeterian innovation + Keynesian demand + Minskyan credit → endogenous business cycles |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  Canvas (spatial) + D3 (charts) + Zustand (state)       │
└────────────────┬────────────────────────────────────────┘
                 │ WebSocket (20 FPS snapshots)
┌────────────────▼────────────────────────────────────────┐
│                  FastAPI Server                          │
│  REST endpoints + WebSocket streaming + async DB         │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│               Simulation Engine                          │
│  Staged Activation: Production → Consumption → Metrics   │
│  AgentSet → do("step") pattern (inspired by Mesa 3)      │
│  Numba JIT for hot-path computation                      │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                 SQLite Database                          │
│  Metrics time series + run metadata + snapshots          │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+ (for frontend)
- uv or pip

### Installation

```bash
# Clone and install
cd tragedy
pip install -e ".[dev]"

# Install frontend dependencies
cd frontend
npm install
```

### CLI: Run a Simulation

```bash
# Run Yard-Sale model with 1000 agents for 5000 ticks
python -m tragedy --model yard_sale --agents 1000 --ticks 5000

# With custom config and output
python -m tragedy --model yard_sale --config configs/yard_sale.yaml --ticks 10000 --output results.csv
```

### Web Server: Real-Time Visualization

```bash
# Terminal 1: Start the API server
tragedy-server
# → http://localhost:8000 (API docs at /docs)

# Terminal 2: Start the frontend
cd frontend
npm run dev
# → http://localhost:5173
```

Then:
1. Open http://localhost:5173 in your browser
2. Click **▶ Start** to launch the Yard-Sale simulation
3. Watch the Lorenz curve animate and the Gini coefficient climb

## Project Structure

```
tragedy/
├── configs/                  # YAML simulation configurations
│   ├── defaults.yaml         # Global default parameters
│   └── yard_sale.yaml        # Yard-Sale model config
├── src/tragedy/
│   ├── core/                 # Simulation engine (Agent, AgentSet, Engine, RNG)
│   ├── economy/              # Economic primitives (Money, Ledger, Markets, Goods)
│   ├── agents/               # Agent type implementations (Household, Firm, Bank)
│   ├── models/               # Model compositions (YardSale, Sugarscape, KS-Macro)
│   ├── markets/              # Market mechanism implementations
│   ├── metrics/              # Numba-accelerated inequality & national metrics
│   ├── api/                  # FastAPI + WebSocket streaming
│   ├── storage/              # SQLite persistence
│   └── utils/                # Config loading, logging
├── frontend/                 # React + Canvas + D3 visualization
│   └── src/components/       # LorenzCurve, DistributionHistogram, TimeSeriesChart
├── tests/                    # pytest suite (unit + integration)
└── docs/                     # Architecture and model documentation
```

## API Reference

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/simulation/start` | Start a new simulation |
| `POST` | `/api/v1/simulation/pause` | Pause the simulation |
| `POST` | `/api/v1/simulation/resume` | Resume a paused simulation |
| `POST` | `/api/v1/simulation/stop` | Stop the simulation |
| `POST` | `/api/v1/simulation/step` | Advance one tick (when paused) |
| `GET` | `/api/v1/simulation/status` | Get current simulation state |
| `GET` | `/api/v1/configs` | List all configurations |
| `POST` | `/api/v1/configs` | Create a new configuration |
| `GET` | `/api/v1/metrics/timeseries` | Query metric time series |
| `GET` | `/api/v1/metrics/latest` | Get latest metrics snapshot |
| `GET` | `/api/v1/metrics/summary` | Get run summary |

### WebSocket

```
ws://localhost:8000/ws/simulation

# Server → Client (snapshot)
{
  "type": "snapshot",
  "tick": 500,
  "metrics": {"gini": 0.42, "total_wealth": 98500, ...},
  "lorenz": {"population": [...], "wealth": [...]},
  "distribution": {"bins": [...], "counts": [...]}
}

# Client → Server (command)
{"type": "command", "action": "pause"}
```

## Yard-Sale Model

The Phase 1 MVP implements the classic Yard-Sale wealth transfer model.

**Configuration** (`configs/yard_sale.yaml`):
```yaml
agents:
  num_households: 1000
  initial_wealth: 100.0

transfer:
  fraction: 0.05    # 5% of poorer agent's wealth
  bias: 0.0         # Fair coin (0 = 50/50)

simulation:
  max_ticks: 5000
  collect_every: 10
```

**Typical Results** (1000 agents, 5000 ticks):
- Gini coefficient: 0.0 → ~0.85
- Top 1% wealth share: ~40%
- Top 10% wealth share: ~70%
- Bottom 50% wealth share: ~5%
- Pareto tail index α: ~1.5

## Implementation Phases

- ✅ **Phase 1 (Current)**: Yard-Sale model + Core engine + Web visualization
- 🔜 **Phase 2**: Sugarscape spatial model with Canvas grid rendering
- 🔜 **Phase 3**: K+S macroeconomic model (firms, banks, government, innovation)
- 🔜 **Phase 4**: Parameter sweeps, C++ acceleration, policy framework

## Development

```bash
# Run tests
pytest

# Run with benchmarks
pytest --benchmark-enable

# Lint
ruff check src/

# Type check
mypy src/
```

## License

MIT
