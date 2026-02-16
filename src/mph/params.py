"""
mph.params
==========
Laden und Validieren der Projektparameter (params.json).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import json

from mph import paths

ALLOWED_STEP_UNITS = {"month", "day", "hour", "quarter"}
ALLOWED_PROCESSED_FORMATS = {"json", "parquet", "csv"}

def load_params(params_path: Optional[Path] = None) -> Dict[str, Any]:
    params_path = params_path or paths.params_json_path()
    with open(params_path, "r", encoding="utf-8") as f:
        params = json.load(f)

    validate_params(params)
    return params

def validate_params(params: Dict[str, Any]) -> None:
    time = params.get("time", {})
    step_unit = time.get("step_unit")
    step_size = int(time.get("step_size", 0))

    if step_unit not in ALLOWED_STEP_UNITS:
        raise ValueError(f"time.step_unit muss in {sorted(ALLOWED_STEP_UNITS)} liegen.")
    if step_size <= 0:
        raise ValueError("time.step_size muss positiv sein.")

    if int(params.get("followup", {}).get("max_months", -1)) != 12:
        raise ValueError("followup.max_months ist fix auf 12.")
    if params.get("model", {}).get("start_state_t0") != "gesund":
        raise ValueError("model.start_state_t0 ist fix auf 'gesund'.")

    io = params.get("io", {})
    fmt = io.get("data_processed_format", "json")
    if fmt not in ALLOWED_PROCESSED_FORMATS:
        raise ValueError(f"io.data_processed_format muss in {sorted(ALLOWED_PROCESSED_FORMATS)} sein.")
