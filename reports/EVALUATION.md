# Verified evaluation

This report records the reproduced reference run against genuine public observations frozen at 31 December 2024. It is not a claim of trading profitability.

## Dataset and split

| Item | Value |
|---|---:|
| Raw joined calendar rows | 7,671 |
| Reported 10-year Treasury observations | 5,254 |
| Development rows after feature windows | 4,940 |
| Untouched 2024 holdout rows | 245 |
| Forecast horizon | 5 trading observations |

The source manifest contains each FRED URL and raw-file SHA-256 checksum. The bundled files were downloaded after the snapshot period and can include corrections made by the publisher; they are not point-in-time vintages.

## Expanding-window selection

| Candidate | Mean validation MAE | Fold standard deviation |
|---|---:|---:|
| Ridge | 0.1322 pp | 0.0062 pp |
| Random Forest | 0.1430 pp | 0.0049 pp |
| Histogram gradient boosting | 0.1478 pp | 0.0155 pp |

Ridge was selected before the 2024 holdout was evaluated.

## 2024 holdout

| Measure | Selected model | Persistence baseline |
|---|---:|---:|
| MAE | 10.257 bp | 10.282 bp |
| RMSE | 12.842 bp | 12.928 bp |
| R² | 0.743 | 0.739 |
| Directional accuracy | 43.0% | 41.0% |

The model improves MAE over persistence by only **0.24%**. This is statistically and commercially marginal, so the honest production decision would be champion/challenger testing rather than automatic replacement of persistence. The result also illustrates why a demanding simple baseline is essential for short-horizon rate forecasts.

## Scenario verification

Scenario `SCN-2024-RATES-100BP` applies a parallel +100 bp Treasury curve shock, +75 bp fed-funds shock and a 25% VIX increase to the latest usable feature row.

| Output | Value |
|---|---:|
| Feature date | 23 December 2024 |
| Baseline five-row-ahead forecast | 4.571% |
| Scenario forecast | 5.080% |
| Model sensitivity | +50.90 bp |
| Baseline/scenario regime | 3 / 3 |

This is a conditional model sensitivity, not a causal estimate or guaranteed price response.

## Monitoring verification

Comparing 2024 with the 2022–2023 reference window produces a **critical** PSI result. The maximum PSI is `8.126` for the 10-year real yield. This is credible because 2024 rate levels differ materially from much of the reference window. A production policy should block automatic promotion and require investigation; it should not suppress this alert merely to produce a green dashboard.

## Quality checks completed

- Four unit/integration tests passed
- Leakage check for future target and lagged feature alignment passed
- Artifact persistence and reload passed
- Scenario identity recalculation passed
- Static lint and source compilation passed
- FastAPI readiness and prediction smoke test passed
- Full download → features → train → evaluate → scenario → monitor workflow passed

