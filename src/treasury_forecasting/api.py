from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from .config import load_config
from .modeling import load_artifacts
from .scenario import apply_shocks


class ForecastRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    features: dict[str, float]
    shocks: dict[str, dict[str, float | str]] = Field(default_factory=dict)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config(os.getenv("TF_CONFIG"))
    artifact_dir = os.getenv("TF_MODEL_DIR", config["paths"]["artifact_dir"])
    try:
        app.state.model, app.state.regime_model, app.state.metadata = load_artifacts(artifact_dir)
        app.state.market_columns = set(config["features"]["market_columns"])
        app.state.ready = True
    except FileNotFoundError:
        app.state.ready = False
    yield


app = FastAPI(title="US Treasury Forecasting API", version="1.0.0", lifespan=lifespan)


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready")
def ready(request: Request) -> dict[str, Any]:
    if not request.app.state.ready:
        raise HTTPException(status_code=503, detail="Model artifacts unavailable")
    return {"status": "ready", "model_version": request.app.state.metadata["version"]}


@app.post("/v1/forecast")
def forecast(payload: ForecastRequest, request: Request) -> dict[str, Any]:
    if not request.app.state.ready:
        raise HTTPException(status_code=503, detail="Model artifacts unavailable")
    metadata = request.app.state.metadata
    missing = sorted(set(metadata["features"]) - set(payload.features))
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing features: {missing}")
    baseline = pd.DataFrame([payload.features])
    scenario = baseline
    if payload.shocks:
        wrapper = {"shocks": payload.shocks}
        try:
            scenario = apply_shocks(baseline, wrapper, request.app.state.market_columns)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    base_prediction = float(request.app.state.model.predict(baseline[metadata["features"]])[0])
    prediction = float(request.app.state.model.predict(scenario[metadata["features"]])[0])
    regime = int(request.app.state.regime_model.predict(scenario[metadata["regime_features"]])[0])
    lower, upper = metadata["prediction_interval_offsets"]
    return {
        "model_version": metadata["version"],
        "forecast_yield_pct": prediction,
        "lower_yield_pct": prediction + lower,
        "upper_yield_pct": prediction + upper,
        "delta_basis_points": (prediction - base_prediction) * 100,
        "regime": regime,
    }
