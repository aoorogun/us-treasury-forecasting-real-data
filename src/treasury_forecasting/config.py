from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    config_path = Path(path) if path else ROOT / "configs" / "base.yaml"
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    with config_path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    for key, value in config["paths"].items():
        path_value = Path(value)
        config["paths"][key] = str(path_value if path_value.is_absolute() else ROOT / path_value)
    return config
