from __future__ import annotations

import argparse
import json

from .config import load_config
from .features import build_features
from .ingestion import download_fred_data, validate_snapshot
from .modeling import train
from .monitoring import monitor
from .scenario import run_scenario


def main() -> None:
    parser = argparse.ArgumentParser(description="US Treasury yield forecasting")
    parser.add_argument("--config")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("download")
    commands.add_parser("train")
    commands.add_parser("evaluate")
    scenario = commands.add_parser("scenario")
    scenario.add_argument("--file", required=True)
    commands.add_parser("monitor")
    args = parser.parse_args()
    config = load_config(args.config)
    if args.command == "download":
        frame = download_fred_data(config)
        quality = validate_snapshot(frame, config)
        build_features(frame, config)
        print(json.dumps(quality, indent=2))
    elif args.command == "train":
        result = train(config)
        print(
            json.dumps(
                {"selected_model": result["selected_model"], "holdout": result["holdout_metrics"]},
                indent=2,
            )
        )
    elif args.command == "evaluate":
        _, _, metadata = __import__(
            "treasury_forecasting.modeling", fromlist=["load_artifacts"]
        ).load_artifacts(config["paths"]["artifact_dir"])
        print(
            json.dumps(
                {
                    "model": metadata["selected_model"],
                    "model_metrics": metadata["holdout_metrics"],
                    "persistence": metadata["persistence_metrics"],
                },
                indent=2,
            )
        )
    elif args.command == "scenario":
        print(json.dumps(run_scenario(config, args.file), indent=2))
    elif args.command == "monitor":
        print(json.dumps(monitor(config), indent=2))


if __name__ == "__main__":
    main()
