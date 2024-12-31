from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FeatureSet:
    frame: pd.DataFrame
    features: list[str]
    target: str


def build_features(raw: pd.DataFrame, config: dict[str, Any], persist: bool = True) -> FeatureSet:
    market = config["features"]["market_columns"]
    horizon = config["data"]["forecast_horizon_rows"]
    max_fill = config["data"]["max_forward_fill_rows"]
    # Treasury trading dates define the modelling calendar.
    frame = raw.loc[raw["treasury_10y"].notna()].copy().sort_values("date")
    flags = []
    for column in market:
        flag = f"{column}__imputed"
        frame[flag] = frame[column].isna().astype("int8")
        frame[column] = frame[column].ffill(limit=max_fill)
        flags.append(flag)
    frame["curve_10y_2y"] = frame["treasury_10y"] - frame["treasury_2y"]
    frame["curve_10y_3m"] = frame["treasury_10y"] - frame["treasury_3m"]
    frame["curve_30y_10y"] = frame["treasury_30y"] - frame["treasury_10y"]
    # Do not include nominal - real - breakeven as a feature: it is an accounting
    # identity in this source and its near-zero variance is numerically unstable.
    derived = ["curve_10y_2y", "curve_10y_3m", "curve_30y_10y"]
    generated_values: dict[str, pd.Series] = {}
    for column in [*market, *derived]:
        for lag in config["features"]["lags"]:
            name = f"{column}__lag_{lag}"
            generated_values[name] = frame[column].shift(lag)
    daily_change = frame["treasury_10y"].diff()
    for window in config["features"]["rolling_windows"]:
        mean = f"treasury_10y__rolling_mean_{window}"
        vol = f"treasury_10y__rolling_vol_{window}"
        generated_values[mean] = frame["treasury_10y"].shift(1).rolling(window).mean()
        generated_values[vol] = daily_change.shift(1).rolling(window).std()
    generated_values["day_of_year_sin"] = np.sin(2 * np.pi * frame["date"].dt.dayofyear / 365.25)
    generated_values["day_of_year_cos"] = np.cos(2 * np.pi * frame["date"].dt.dayofyear / 365.25)
    generated_frame = pd.DataFrame(generated_values, index=frame.index)
    frame = pd.concat([frame, generated_frame], axis=1)
    generated = list(generated_values)
    target = f"treasury_10y_t_plus_{horizon}"
    frame[target] = frame["treasury_10y"].shift(-horizon)
    features = [*market, *flags, *derived, *generated]
    frame = frame.dropna(subset=[*features, target]).reset_index(drop=True)
    if persist:
        path = Path(config["paths"]["processed"])
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
    return FeatureSet(frame, features, target)
