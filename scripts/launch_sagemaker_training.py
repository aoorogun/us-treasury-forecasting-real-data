"""Submit the reproducible training workflow to SageMaker."""

from __future__ import annotations

import os


def main() -> None:
    try:
        from sagemaker.sklearn.estimator import SKLearn
    except ImportError as exc:
        raise SystemExit("Install with: pip install -e '.[aws]'") from exc
    estimator = SKLearn(
        entry_point="scripts/train_job.py",
        source_dir=".",
        role=os.environ["SAGEMAKER_ROLE_ARN"],
        instance_type="ml.m5.xlarge",
        instance_count=1,
        framework_version="1.2-1",
        py_version="py3",
        base_job_name="treasury-forecasting",
    )
    estimator.fit(wait=True, logs=True)


if __name__ == "__main__":
    main()
