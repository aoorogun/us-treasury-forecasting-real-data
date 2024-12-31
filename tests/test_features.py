from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from treasury_forecasting.config import load_config
from treasury_forecasting.features import build_features


class FeatureTests(unittest.TestCase):
    def test_target_is_future_value_and_features_are_past_only(self) -> None:
        config = load_config()
        config["data"]["forecast_horizon_rows"] = 2
        config["features"]["lags"] = [1, 2]
        config["features"]["rolling_windows"] = [2]
        dates = pd.bdate_range("2020-01-01", periods=20)
        values = np.arange(20, dtype=float) + 2
        raw = pd.DataFrame({"date": dates})
        for column in config["features"]["market_columns"]:
            raw[column] = values if column != "vix" else values + 10
        result = build_features(raw, config, persist=False).frame
        first = result.iloc[0]
        original_index = raw.index[raw["date"] == first["date"]][0]
        self.assertEqual(first["treasury_10y__lag_1"], raw.loc[original_index - 1, "treasury_10y"])
        self.assertEqual(
            first[result.columns[result.columns.str.startswith("treasury_10y_t_plus")][0]],
            raw.loc[original_index + 2, "treasury_10y"],
        )


if __name__ == "__main__":
    unittest.main()
