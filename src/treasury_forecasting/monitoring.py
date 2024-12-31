from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def psi(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    ref = pd.to_numeric(reference, errors="coerce").dropna().to_numpy()
    cur = pd.to_numeric(current, errors="coerce").dropna().to_numpy()
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    ref_pct = np.clip(np.histogram(ref, bins=edges)[0] / len(ref), 1e-6, None)
    cur_pct = np.clip(np.histogram(cur, bins=edges)[0] / len(cur), 1e-6, None)
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def monitor(config: dict[str, Any]) -> dict[str, Any]:
    frame = pd.read_csv(config["paths"]["processed"], parse_dates=["date"])
    mcfg = config["monitoring"]
    reference = frame.loc[frame["date"].between(mcfg["reference_start"], mcfg["reference_end"])]
    current = frame.loc[frame["date"] >= pd.Timestamp(mcfg["current_start"])]
    scores = {
        column: psi(reference[column], current[column])
        for column in config["features"]["market_columns"]
    }
    maximum = max(scores.values())
    status = (
        "critical"
        if maximum >= mcfg["psi_critical"]
        else "warning"
        if maximum >= mcfg["psi_warning"]
        else "healthy"
    )
    result = {
        "status": status,
        "maximum_psi": maximum,
        "feature_psi": scores,
        "reference_rows": len(reference),
        "current_rows": len(current),
        "action": "investigate before promotion" if status == "critical" else "continue monitoring",
    }
    report_dir = Path(config["paths"]["report_dir"])
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "drift_report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
