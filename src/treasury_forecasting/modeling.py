from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .features import FeatureSet, build_features
from .ingestion import load_raw_snapshot, sha256, validate_snapshot


def estimator(name: str, seed: int) -> Any:
    if name == "ridge":
        return Pipeline([("scale", StandardScaler()), ("model", Ridge(alpha=8.0))])
    if name == "random_forest":
        return RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=5,
            max_features=0.65,
            n_jobs=-1,
            random_state=seed,
        )
    if name == "hist_gradient_boosting":
        return HistGradientBoostingRegressor(
            learning_rate=0.05,
            max_iter=300,
            max_leaf_nodes=25,
            l2_regularization=0.3,
            random_state=seed,
        )
    raise ValueError(f"Unknown candidate: {name}")


def metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae_pct_points": float(mean_absolute_error(actual, predicted)),
        "mae_basis_points": float(mean_absolute_error(actual, predicted) * 100),
        "rmse_pct_points": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
        "directional_accuracy": float(
            np.mean(np.sign(predicted[1:] - actual[:-1]) == np.sign(actual[1:] - actual[:-1]))
        ),
    }


def expanding_folds(frame: pd.DataFrame, holdout_start: str, folds: int, days: int):
    development = frame.loc[frame["date"] < pd.Timestamp(holdout_start)]
    end = len(development)
    for fold in range(folds, 0, -1):
        validation_end = end - (fold - 1) * days
        validation_start = validation_end - days
        yield development.iloc[:validation_start], development.iloc[validation_start:validation_end]


def train(config: dict[str, Any]) -> dict[str, Any]:
    raw = load_raw_snapshot(config)
    quality = validate_snapshot(raw, config)
    feature_set: FeatureSet = build_features(raw, config)
    frame, features, target = feature_set.frame, feature_set.features, feature_set.target
    holdout_start = config["data"]["holdout_start"]
    seed = config["project"]["seed"]
    cv: dict[str, list[float]] = {name: [] for name in config["training"]["candidates"]}
    for train_frame, validation_frame in expanding_folds(
        frame,
        holdout_start,
        config["training"]["validation_folds"],
        config["training"]["validation_days"],
    ):
        for name in cv:
            model = estimator(name, seed)
            model.fit(train_frame[features], train_frame[target])
            cv[name].append(
                mean_absolute_error(
                    validation_frame[target], model.predict(validation_frame[features])
                )
            )
    cv_summary = {
        name: {
            "fold_mae": values,
            "mean_mae": float(np.mean(values)),
            "std_mae": float(np.std(values)),
        }
        for name, values in cv.items()
    }
    selected = min(cv_summary, key=lambda name: cv_summary[name]["mean_mae"])
    development = frame.loc[frame["date"] < pd.Timestamp(holdout_start)]
    holdout = frame.loc[frame["date"] >= pd.Timestamp(holdout_start)]
    model = estimator(selected, seed)
    model.fit(development[features], development[target])
    prediction = model.predict(holdout[features])
    test_metrics = metrics(holdout[target].to_numpy(), prediction)
    persistence = holdout["treasury_10y"].to_numpy()
    persistence_metrics = metrics(holdout[target].to_numpy(), persistence)

    residuals = holdout[target].to_numpy() - prediction
    alpha = config["training"]["interval_alpha"]
    intervals = [
        float(np.quantile(residuals, alpha / 2)),
        float(np.quantile(residuals, 1 - alpha / 2)),
    ]

    regime_features = ["curve_10y_2y", "curve_10y_3m", "vix", "treasury_10y__rolling_vol_21"]
    regime_pipeline = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "cluster",
                KMeans(
                    n_clusters=config["training"]["regime_clusters"], random_state=seed, n_init=20
                ),
            ),
        ]
    )
    regime_pipeline.fit(development[regime_features])
    holdout_regime = regime_pipeline.predict(holdout[regime_features])

    output = holdout[["date", "treasury_10y", target]].copy()
    output["predicted_treasury_10y"] = prediction
    output["persistence_prediction"] = persistence
    output["regime"] = holdout_regime
    artifact_dir = Path(config["paths"]["artifact_dir"])
    report_dir = Path(config["paths"]["report_dir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, artifact_dir / "forecast_model.joblib")
    joblib.dump(regime_pipeline, artifact_dir / "regime_model.joblib")
    output.to_csv(report_dir / "holdout_predictions.csv", index=False)
    metadata = {
        "version": config["project"]["version"],
        "selected_model": selected,
        "forecast_horizon_rows": config["data"]["forecast_horizon_rows"],
        "target": target,
        "features": features,
        "regime_features": regime_features,
        "cross_validation": cv_summary,
        "holdout_metrics": test_metrics,
        "persistence_metrics": persistence_metrics,
        "prediction_interval_offsets": intervals,
        "holdout_start": holdout_start,
        "holdout_end": str(holdout["date"].max().date()),
        "development_rows": len(development),
        "holdout_rows": len(holdout),
        "data_quality": quality,
        "processed_sha256": sha256(Path(config["paths"]["processed"])),
    }
    (artifact_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def load_artifacts(artifact_dir: str | Path):
    path = Path(artifact_dir)
    return (
        joblib.load(path / "forecast_model.joblib"),
        joblib.load(path / "regime_model.joblib"),
        json.loads((path / "metadata.json").read_text(encoding="utf-8")),
    )
