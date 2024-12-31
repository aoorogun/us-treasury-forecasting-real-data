# US Treasury Yield Forecasting with Real-World Data

A production-style data science project that ingests public market observations, forecasts the US 10-year Treasury yield five business days ahead, identifies market regimes, and reforecasts under proposed financial shocks.

The bundled snapshot contains genuine observations from FRED, frozen at **31 December 2024**. This is an educational portfolio project, not investment advice.

## Evidence against the role requirements

| Requirement | Repository evidence |
|---|---|
| Multivariate predictive ML | Ridge, Random Forest and histogram gradient boosting using the Treasury curve, policy rate, real yield, inflation expectations and volatility |
| Supervised and unsupervised ML | Yield regression plus K-Means market-regime discovery |
| Dynamic reforecasting | Scenario engine applies rate, inflation and volatility shocks and calculates scenario-minus-baseline impact |
| Robust ML pipelines | Source manifest, checksums, schema/range checks, leakage-safe features, rolling-origin backtesting and immutable artifacts |
| Deep learning | Optional PyTorch temporal MLP module with early stopping-ready architecture |
| AWS/SageMaker | Container, inference contract, pipeline design, CloudFormation and OIDC deployment workflow |
| Production operations | FastAPI, health checks, drift/performance monitoring, model card, runbook and CI |

## Data

Daily observations are downloaded from the Federal Reserve Bank of St. Louis FRED graph endpoint:

- `DGS3MO`, `DGS2`, `DGS10`, `DGS30`: Treasury constant maturity yields
- `DFF`: effective federal funds rate
- `DFII10`: 10-year Treasury inflation-indexed yield
- `T10YIE`: 10-year breakeven inflation rate
- `VIXCLS`: CBOE Volatility Index

The project uses only dates where the 10-year yield is reported. Other series are forward-filled with a strict five-business-day limit, and imputation flags are included as model features. See [DATA_SOURCES.md](docs/DATA_SOURCES.md) for provenance and usage notes.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

treasury-forecast download
treasury-forecast train
treasury-forecast evaluate
treasury-forecast scenario --file configs/scenario_rate_shock.json
treasury-forecast monitor
python -m unittest discover -s tests -v
```

Start the service:

```bash
uvicorn treasury_forecasting.api:app --host 0.0.0.0 --port 8080
```

## Forecast design

- **Target:** closing 10-year Treasury constant-maturity yield five business rows ahead, in percentage points.
- **Cutoff discipline:** every feature at row `t` is known on or before `t`; the target is shifted backward from `t+5`.
- **Validation:** expanding-window folds select the model using pre-2024 history.
- **Final holdout:** calendar year 2024 is untouched until the final model is chosen.
- **Baselines:** no-change/persistence and a rolling-mean forecast.
- **Decision output:** baseline, shocked scenario, absolute basis-point impact and scenario metadata.

## Repository structure

```text
data/raw/                 immutable downloaded series and source manifest
data/processed/           joined modelling table
src/treasury_forecasting/ ingestion, features, models, scenarios, monitoring, API
tests/                    unit and integration tests
artifacts/                fitted model, regime model and metadata
reports/                  verified holdout and scenario results
infra/                    AWS reference infrastructure
docs/                     architecture, model card, data sources and runbook
```

## Important limitations

This is a forecasting and sensitivity tool, not a trading system. FRED data can be revised, and the bundled files are a reproducible snapshot rather than a point-in-time vintage database. Scenario deltas are model sensitivities—not causal estimates or guaranteed market moves.

