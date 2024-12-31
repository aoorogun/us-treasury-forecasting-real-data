# Model card

## Purpose

Forecast the US 10-year Treasury constant-maturity yield five trading observations ahead and provide transparent model sensitivities to financial shocks. Intended users are planning, treasury and model-risk teams.

## Not intended for

- Automated trading, order generation or investment advice
- Valuation without an independently validated pricing model
- Causal claims about policy or proposed decisions
- Use outside observed market ranges without expert challenge

## Model families

Ridge regression, Random Forest and histogram gradient boosting are compared using expanding-window validation. K-Means assigns descriptive market regimes from curve slopes, VIX and recent 10-year-yield volatility. The cluster numbers have no inherent ordering and must be profiled before receiving business labels.

## Metrics and gates

- MAE and RMSE in percentage points and basis points
- R² and directional accuracy as secondary diagnostics
- Performance compared with a no-change persistence forecast
- Fold mean and standard deviation reported for stability
- Final acceptance requires a meaningful business advantage over persistence or an explicit decision to retain persistence

## Limitations

- The forecast horizon is five observations, not guaranteed calendar days.
- Revised data are not equivalent to information available in real time.
- Correlated yield-curve features can reduce coefficient interpretability.
- Regimes describe statistical similarity, not economic truth.
- Prediction intervals use empirical holdout residuals in this reference build; production calibration must use a separate calibration window.
- Extreme events may sit outside training support.

## Governance

Every artifact is linked to a processed-data checksum, configuration, model version, validation results and source manifest. Promotion requires model-owner and risk approval. Monitor source freshness, missingness, PSI, prediction distribution, interval coverage, realised error and scenario volumes. Critical drift blocks automatic promotion.

