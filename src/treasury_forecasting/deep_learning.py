"""Optional PyTorch temporal MLP for controlled challenger experiments."""

from __future__ import annotations

from typing import Any


def build_temporal_mlp(input_dim: int) -> Any:
    try:
        import torch.nn as nn
    except ImportError as exc:  # pragma: no cover
        raise ImportError("Install with: pip install -e '.[deep-learning]'") from exc
    return nn.Sequential(
        nn.Linear(input_dim, 256),
        nn.BatchNorm1d(256),
        nn.GELU(),
        nn.Dropout(0.25),
        nn.Linear(256, 64),
        nn.GELU(),
        nn.Dropout(0.1),
        nn.Linear(64, 1),
    )
