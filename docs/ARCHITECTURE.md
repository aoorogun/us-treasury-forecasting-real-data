# Architecture

```text
FRED endpoints -> immutable raw CSVs + checksums -> validation -> joined trading calendar
                                                                  |
                                    lags, curve slopes, rolling levels/volatility
                                                                  |
                       expanding-window model selection + 2024 holdout
                          |                       |
                 yield regression          K-Means regimes
                          |                       |
                 versioned artifacts + metadata + evaluation report
                          |
          FastAPI / SageMaker endpoint <- scenario shocks -> impact response
                          |
               drift + realised-error monitoring -> CloudWatch
```

## Leakage controls

- The target is the observed 10-year yield five trading rows after the feature row.
- Lagged values are shifted explicitly; rolling means and volatilities are shifted before aggregation.
- Candidate models are compared on expanding-window folds.
- Calendar year 2024 is excluded from both fitting and model selection.
- The scenario engine updates contemporaneous shocked inputs and their direct curve identities, but never rewrites historical lags.

## AWS production design

EventBridge starts a SageMaker Pipeline after the daily source window. Processing validates and materialises features in encrypted, versioned S3. Training jobs record experiments and lineage. An evaluation step applies regression, baseline, interval and regime checks before a package can enter Model Registry. Approved versions deploy canary traffic to a private SageMaker endpoint; large reforecasts use Batch Transform. Model Monitor and custom realised-error jobs publish CloudWatch metrics and alerts.

## Scaling and reliability

The online API is stateless and accepts one complete feature vector per request. A production feature store should serve point-in-time feature rows. Requests are idempotent by scenario ID and source snapshot. Invalid or stale source data stops a new run; the last approved forecast remains available. Endpoint rollback uses the prior immutable model package and container digest.

