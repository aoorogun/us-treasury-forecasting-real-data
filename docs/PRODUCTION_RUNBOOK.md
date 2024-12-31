# Production runbook

## Scheduled run

1. Download source series into a new immutable snapshot prefix.
2. Verify TLS, response type, dates, row counts, duplicate keys, ranges and checksum manifest.
3. Build features with the configured forward-fill limit.
4. Score with the current approved model.
5. Publish the forecast with source date, model version and interval.
6. When outcomes mature, calculate realised error and interval coverage.

## Retraining

Retrain monthly or after two consecutive accuracy breaches, critical drift, a change in source methodology, or material market regime change. Retraining is automated; promotion is not. The challenger must complete backtests and pass approval.

## Incident response

- **Source unavailable:** retry with backoff, alert after the source window, and retain the last forecast with a stale-data label.
- **Schema/range failure:** quarantine the snapshot; never silently coerce an unexplained break.
- **Accuracy breach:** compare source revisions, regime mix and feature drift; run champion/challenger analysis.
- **Endpoint failure:** shift traffic to the previous endpoint configuration and verify a golden prediction.
- **Critical drift:** stop promotion, notify model owner and risk, and document the disposition.

## Security

Use GitHub OIDC rather than static AWS keys. Keep SageMaker in private subnets with VPC endpoints. Encrypt S3/EBS with KMS, block public access, use least-privilege roles, log access in CloudTrail and scan images/dependencies. Do not place credentials in source or model artifacts.

## Service objectives

| Measure | Objective |
|---|---:|
| Online availability | 99.9% monthly |
| p95 single-request latency | < 300 ms |
| Daily forecast delivery | before 08:00 New York time |
| Source freshness | previous market close |
| Critical alert acknowledgement | < 30 minutes |

