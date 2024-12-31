from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


def model_fn(model_dir: str) -> dict[str, Any]:
    path = Path(model_dir)
    return {
        "model": joblib.load(path / "forecast_model.joblib"),
        "regime": joblib.load(path / "regime_model.joblib"),
        "metadata": json.loads((path / "metadata.json").read_text(encoding="utf-8")),
    }


def input_fn(body: str, content_type: str) -> pd.DataFrame:
    if content_type != "application/json":
        raise ValueError("Only application/json is supported")
    records = json.loads(body).get("records", [])
    if not records:
        raise ValueError("records must be a non-empty list")
    return pd.DataFrame(records)


def predict_fn(data: pd.DataFrame, bundle: dict[str, Any]) -> dict[str, Any]:
    metadata = bundle["metadata"]
    missing = sorted(set(metadata["features"]) - set(data.columns))
    if missing:
        raise ValueError(f"Missing features: {missing}")
    values = bundle["model"].predict(data[metadata["features"]])
    regimes = bundle["regime"].predict(data[metadata["regime_features"]])
    return {
        "model_version": metadata["version"],
        "forecast_yield_pct": values.tolist(),
        "regime": regimes.tolist(),
    }


def output_fn(result: dict[str, Any], accept: str) -> tuple[str, str]:
    if accept != "application/json":
        raise ValueError("Only application/json is supported")
    return json.dumps(result), accept
