"""SageMaker training entry point."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from treasury_forecasting.config import load_config  # noqa: E402
from treasury_forecasting.modeling import train  # noqa: E402


def main() -> None:
    metadata = train(load_config())
    print(json.dumps(metadata["holdout_metrics"], indent=2))


if __name__ == "__main__":
    main()
