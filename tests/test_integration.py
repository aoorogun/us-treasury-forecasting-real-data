from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from treasury_forecasting.config import load_config
from treasury_forecasting.modeling import load_artifacts, train


class IntegrationTests(unittest.TestCase):
    def test_bundled_snapshot_trains_and_persists_artifacts(self) -> None:
        config = load_config()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config["paths"]["processed"] = str(root / "processed.csv")
            config["paths"]["artifact_dir"] = str(root / "artifacts")
            config["paths"]["report_dir"] = str(root / "reports")
            config["training"]["candidates"] = ["ridge"]
            config["training"]["validation_folds"] = 2
            metadata = train(config)
            model, regime_model, loaded = load_artifacts(config["paths"]["artifact_dir"])
            self.assertIsNotNone(model)
            self.assertIsNotNone(regime_model)
            self.assertEqual(metadata["processed_sha256"], loaded["processed_sha256"])
            self.assertGreater(metadata["holdout_rows"], 200)


if __name__ == "__main__":
    unittest.main()
