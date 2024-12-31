from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from treasury_forecasting.monitoring import psi
from treasury_forecasting.scenario import apply_shocks


class ScenarioMonitoringTests(unittest.TestCase):
    def test_curve_features_are_recomputed_after_shock(self) -> None:
        frame = pd.DataFrame(
            {
                "treasury_3m": [4.0],
                "treasury_2y": [4.2],
                "treasury_10y": [4.5],
                "treasury_30y": [4.7],
                "real_yield_10y": [2.0],
                "breakeven_10y": [2.4],
                "vix": [15.0],
                "curve_10y_2y": [0.3],
                "curve_10y_3m": [0.5],
                "curve_30y_10y": [0.2],
                "real_plus_breakeven_gap": [-0.1],
            }
        )
        scenario = {"shocks": {"treasury_10y": {"operation": "add", "value": 1.0}}}
        result = apply_shocks(frame, scenario, {"treasury_10y"})
        self.assertAlmostEqual(result["curve_10y_2y"].iloc[0], 1.3)
        self.assertAlmostEqual(result["curve_30y_10y"].iloc[0], -0.8)

    def test_psi_detects_material_shift(self) -> None:
        rng = np.random.default_rng(42)
        reference = pd.Series(rng.normal(0, 1, 3000))
        stable = pd.Series(rng.normal(0, 1, 3000))
        shifted = pd.Series(rng.normal(1.5, 1, 3000))
        self.assertLess(psi(reference, stable), 0.1)
        self.assertGreater(psi(reference, shifted), 0.25)


if __name__ == "__main__":
    unittest.main()
