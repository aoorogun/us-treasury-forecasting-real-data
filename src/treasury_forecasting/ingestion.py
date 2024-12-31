from __future__ import annotations

import hashlib
import json
import ssl
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.request import urlopen

import certifi
import pandas as pd

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_text(url: str) -> str:
    context = ssl.create_default_context(cafile=certifi.where())
    with urlopen(url, timeout=60, context=context) as response:  # noqa: S310
        return response.read().decode("utf-8")


def download_fred_data(config: dict[str, Any]) -> pd.DataFrame:
    """Download individual FRED series, persist raw files, and produce an outer join."""
    data_cfg = config["data"]
    raw_dir = Path(config["paths"]["raw_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []
    manifest: dict[str, Any] = {
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "snapshot_cutoff": data_cfg["end"],
        "provider": "Federal Reserve Bank of St. Louis FRED",
        "series": {},
    }
    for series_id, column in data_cfg["series"].items():
        url = f"{FRED_CSV}?id={series_id}&cosd={data_cfg['start']}&coed={data_cfg['end']}"
        text = _download_text(url)
        frame = pd.read_csv(StringIO(text), na_values=["."])
        frame.columns = ["date", column]
        frame["date"] = pd.to_datetime(frame["date"])
        raw_path = raw_dir / f"{series_id}.csv"
        raw_path.write_text(text, encoding="utf-8")
        manifest["series"][series_id] = {
            "column": column,
            "url": url,
            "rows": len(frame),
            "sha256": sha256(raw_path),
        }
        frames.append(frame)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="date", how="outer")
    merged = merged.sort_values("date").reset_index(drop=True)
    (raw_dir / "source_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return merged


def load_raw_snapshot(config: dict[str, Any]) -> pd.DataFrame:
    raw_dir = Path(config["paths"]["raw_dir"])
    frames = []
    for series_id, column in config["data"]["series"].items():
        path = raw_dir / f"{series_id}.csv"
        frame = pd.read_csv(path, parse_dates=["observation_date"], na_values=["."])
        frame.columns = ["date", column]
        frames.append(frame)
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="date", how="outer")
    return merged.sort_values("date").reset_index(drop=True)


def validate_snapshot(frame: pd.DataFrame, config: dict[str, Any]) -> dict[str, Any]:
    expected = {"date", *config["data"]["series"].values()}
    missing = expected - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if frame["date"].duplicated().any():
        raise ValueError("Duplicate observation dates detected")
    if frame["date"].max() > pd.Timestamp(config["data"]["end"]):
        raise ValueError("Snapshot contains observations after configured cutoff")
    if frame["treasury_10y"].notna().sum() < 4000:
        raise ValueError("Insufficient 10-year Treasury observations")
    yields = [c for c in frame if "treasury" in c or c in {"fed_funds", "real_yield_10y"}]
    for column in yields:
        values = frame[column].dropna()
        if not values.between(-5, 25).all():
            raise ValueError(f"Out-of-range value detected in {column}")
    return {
        "rows": len(frame),
        "start": str(frame["date"].min().date()),
        "end": str(frame["date"].max().date()),
        "ten_year_observations": int(frame["treasury_10y"].notna().sum()),
    }
