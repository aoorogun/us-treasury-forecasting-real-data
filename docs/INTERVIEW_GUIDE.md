# Interview guide

## Two-minute walkthrough

“This project uses real public market data rather than synthetic records. I built a reproducible FRED ingestion layer with per-series checksums and a fixed 2024 cutoff. The supervised task predicts the 10-year Treasury yield five trading observations ahead from the curve, policy rate, real yield, inflation expectations and VIX. All feature windows are shifted, model selection uses expanding time folds, and 2024 is a final holdout. I benchmark against persistence because short-horizon yields are difficult to beat. I also use K-Means for descriptive market regimes. Proposed shocks are applied only to contemporaneous financial variables; dependent curve features are recalculated, while historical lags remain untouched. The same artifacts serve through FastAPI or SageMaker, with drift monitoring, CI/CD, governance and rollback controls.”

## Strong discussion points

**Why is persistence a demanding baseline?**  
Yields are highly autocorrelated and short-horizon changes are noisy. A complex model that does not beat no-change is not adding forecasting value.

**Why not random cross-validation?**  
It trains on future regimes and creates unrealistic leakage. Expanding windows reproduce how the model would have been used through time.

**Are the scenario impacts causal?**  
No. They are model sensitivities conditional on changed inputs. A causal effect requires a separate identification strategy.

**What would you change for live trading use?**  
Use point-in-time vintages, precise release timestamps, transaction costs, executable prices, stronger backtesting controls and independent model validation. This repository explicitly does not claim trading readiness.

**Why include Ridge?**  
It extrapolates, is stable under correlated curve features and provides a valuable bias/variance counterpoint to nonlinear trees.

## Extensions

- ALFRED vintage data and release-lag modelling
- Quantile or conformal forecasts with separate calibration data
- Temporal Fusion Transformer or LSTM challenger at larger scale
- SHAP diagnostics and monotonic constraints
- Hierarchical multi-horizon forecasts across the yield curve
- Champion/challenger shadow endpoints and automatic rollback metrics

