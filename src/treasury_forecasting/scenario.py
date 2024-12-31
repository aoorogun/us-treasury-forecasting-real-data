from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .modeling import load_artifacts

OPERATIONS = {"add", "multiply", "set"}


def load_scenario(path: str | Path) -> dict[str, Any]:
    scenario = json.loads(Path(path).read_text(encoding="utf-8"))
    if scenario.get("status") not in {"proposed", "committed"}:
        raise ValueError("status must be proposed or committed")
    for feature, shock in scenario.get("shocks", {}).items():
        if shock.get("operation") not in OPERATIONS:
            raise ValueError(f"Unsupported operation for {feature}")
        if not isinstance(shock.get("value"), (int, float)):
            raise ValueError(f"Shock for {feature} must be numeric")
    return scenario


def apply_shocks(row: pd.DataFrame, scenario: dict[str, Any], allowed: set[str]) -> pd.DataFrame:
    shocked = row.copy()
    for feature, shock in scenario["shocks"].items():
        if feature not in allowed:
            raise ValueError(f"Feature cannot be shocked: {feature}")
        operation, value = shock["operation"], shock["value"]
        if operation == "add":
            shocked[feature] += value
        elif operation == "multiply":
            shocked[feature] *= value
        else:
            shocked[feature] = value
    # Recompute directly-dependent curve features while leaving historical lags unchanged.
    shocked["curve_10y_2y"] = shocked["treasury_10y"] - shocked["treasury_2y"]
    shocked["curve_10y_3m"] = shocked["treasury_10y"] - shocked["treasury_3m"]
    shocked["curve_30y_10y"] = shocked["treasury_30y"] - shocked["treasury_10y"]
    return shocked


def run_scenario(config: dict[str, Any], scenario_path: str | Path) -> dict[str, Any]:
    scenario = load_scenario(scenario_path)
    processed = pd.read_csv(config["paths"]["processed"], parse_dates=["date"])
    as_of = pd.Timestamp(scenario["as_of"])
    eligible = processed.loc[processed["date"] <= as_of]
    if eligible.empty:
        raise ValueError("No feature row is available on or before scenario as_of")
    baseline_row = eligible.tail(1)
    model, regime_model, metadata = load_artifacts(config["paths"]["artifact_dir"])
    allowed = set(config["features"]["market_columns"])
    shocked_row = apply_shocks(baseline_row, scenario, allowed)
    base = float(model.predict(baseline_row[metadata["features"]])[0])
    shocked = float(model.predict(shocked_row[metadata["features"]])[0])
    base_regime = int(regime_model.predict(baseline_row[metadata["regime_features"]])[0])
    shocked_regime = int(regime_model.predict(shocked_row[metadata["regime_features"]])[0])
    result = {
        "scenario_id": scenario["scenario_id"],
        "status": scenario["status"],
        "requested_as_of": scenario["as_of"],
        "feature_date": str(baseline_row["date"].iloc[0].date()),
        "model_version": metadata["version"],
        "baseline_yield_pct": base,
        "scenario_yield_pct": shocked,
        "delta_basis_points": (shocked - base) * 100,
        "baseline_regime": base_regime,
        "scenario_regime": shocked_regime,
        "shocks": scenario["shocks"],
    }
    report_dir = Path(config["paths"]["report_dir"])
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "scenario_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
