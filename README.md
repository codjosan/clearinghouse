# ClearingLab — Cross-Asset Derivatives Portfolio Margin & Clearinghouse

ClearingLab is an offline, deterministic Python 3.10+ quantitative engineering project implementing a cross-asset cryptocurrency derivatives clearinghouse and portfolio margin risk engine. It supports perpetual futures (`PERP`) and European options (`CALL`, `PUT`) across **BTC**, **ETH**, **SOL**, and **AVAX** within unified cross-margin accounts.

Built purely on the Python standard library with zero external dependencies or network calls, the codebase provides market data ingestion, Black–Scholes analytical pricing and Greeks, implied volatility solving, double-entry cash and position accounting, deterministic event replay, scenario stress testing, and a structured clearing engine interface.

## Project Structure

```text
clearinghouse_risk_challenge/
├── README.md                  # Project overview, commands, and test instructions
├── data/                      # Deterministic synthetic market and event dataset
│   ├── DATA_DICTIONARY.md     # Schema and field descriptions for dataset files
│   ├── events.csv             # 4,763 chronological account events (deposits, fills, funding)
│   ├── index.csv              # 720 daily underlying index prices
│   ├── instruments.csv        # 164 contract specifications (perpetuals and European options)
│   ├── manifest.json          # Dataset metadata, seed, and train/validation/test day splits
│   └── marks.csv              # 29,520 daily bid/mid/ask and implied volatility snapshots
├── scripts/                   # Command-line execution, audit, and verification scripts
│   ├── audit_data.py          # Validates dataset integrity, schemas, and chronological order
│   ├── check_acceptance.py    # Verifies clearing engine interface and gate checks
│   ├── generate_data.py       # Reproducible synthetic market and event data generator
│   ├── run_candidate.py       # Runs deterministic replay using CandidateClearingEngine
│   ├── run_reference.py       # Runs deterministic replay using the baseline ReferenceMargin
│   ├── run_stress_matrix.py   # Evaluates 12 stress scenarios across accounts and checkpoints
│   └── run_tests.py           # Discovers and executes the unit test suite
├── src/clearinglab/           # Core clearinghouse and risk engine package
│   ├── __init__.py            # Package metadata and version
│   ├── candidate.py           # CandidateClearingEngine (margin, pre-trade, liquidation, reconciliation)
│   ├── ledger.py              # Double-entry cash journal, cost-basis tracking, and replay
│   ├── market.py              # Market snapshot loader and quote validation
│   ├── pricing.py             # Black–Scholes pricing, analytical Greeks, and implied volatility solver
│   ├── reference_margin.py    # Baseline scenario-based portfolio margin calculator
│   ├── replay.py              # Chronological multi-day event replay runner
│   ├── scenarios.py           # 12 deterministic spot, volatility, correlation, and liquidity shocks
│   ├── types.py               # Core domain dataclasses (Instrument, Position, Account, RiskReport, etc.)
│   └── validation.py          # Risk report and engine interface validation helpers
└── tests/                     # Unit and integration test suite
    ├── test_full_replay.py    # End-to-end 180-day replay determinism and ledger balance tests
    ├── test_ledger.py         # Double-entry accounting, cost basis, funding, and idempotency tests
    ├── test_market_and_margin.py # Market quotes, stress scenarios, and margin evaluation tests
    ├── test_pricing.py        # Put-call parity, boundary conditions, Greeks, and IV solver tests
    ├── test_replay.py         # Multi-day replay window and journal equivalence tests
    └── test_validation.py     # Risk report finiteness and invariant checks
```

## Requirements

- **Python:** 3.10 or higher
- **Dependencies:** Python standard library only (`csv`, `json`, `math`, `decimal`, `hashlib`, `dataclasses`, `unittest`, etc.)

## Script Commands

Run all commands from the repository root (`clearinghouse_risk_challenge/`):

1. **Audit the synthetic dataset** (verifies row counts, unique IDs, mark spreads, and chronological event ordering):
   ```bash
   python scripts/audit_data.py
   ```

2. **Run the reference market replay** (replays all 4,763 events across 180 days using `ReferenceMargin` and writes `outputs/reference/replay_summary.json`):
   ```bash
   python scripts/run_reference.py
   ```

3. **Run the candidate clearing engine replay** (replays events using `CandidateClearingEngine` and writes `outputs/candidate/replay_summary.json`):
   ```bash
   python scripts/run_candidate.py
   ```

4. **Run the multi-scenario stress matrix** (evaluates all 12 shock scenarios across 120 accounts at 12 checkpoints and writes outputs to `outputs/stress/`):
   ```bash
   python scripts/run_stress_matrix.py
   ```

5. **Run the acceptance verification gate** (checks risk report invariants and engine methods `evaluate`, `pretrade`, `liquidate`, and `reconcile`, writing `outputs/acceptance/starter_gate.json`):
   ```bash
   python scripts/check_acceptance.py
   ```
   *(Note: In the initial baseline state, `pretrade`, `liquidate`, and `reconcile` raise `NotImplementedError` until implemented in `src/clearinglab/candidate.py`.)*

6. **Regenerate synthetic market data** (optional; reproduces `data/` using a deterministic PRNG seed):
   ```bash
   python scripts/generate_data.py --out data --seed 20261124
   ```

## Running Tests

Execute the full unit and integration test suite using the runner script:

```bash
python scripts/run_tests.py
```

Alternatively, invoke Python's `unittest` runner directly with `src` on `PYTHONPATH`:

```bash
# macOS / Linux
PYTHONPATH=src python -m unittest discover -s tests -v

# Windows PowerShell
$env:PYTHONPATH='src'; python -m unittest discover -s tests -v
```
