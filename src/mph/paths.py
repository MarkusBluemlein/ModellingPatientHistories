"""
mph.paths
=========
Zentrale Pfadfunktionen für das Repository "ModellingPatientHistories".
"""

from __future__ import annotations
from pathlib import Path

def project_root() -> Path:
    """Ermittelt das Root-Verzeichnis des Repositories (robust über Marker)."""
    here = Path(__file__).resolve()
    for p in [here.parent] + list(here.parents):
        if (p / "params.json").exists() and (p / "src").exists() and (p / "data").exists():
            return p
    return here.parents[2]

def src_dir() -> Path:
    return project_root() / "src"

def mph_dir() -> Path:
    return src_dir() / "mph"

def data_dir() -> Path:
    return project_root() / "data"

def processed_dir() -> Path:
    return data_dir() / "processed"

def notebooks_dir() -> Path:
    return project_root() / "notebooks"

def outputs_dir() -> Path:
    return project_root() / "outputs"

def params_json_path() -> Path:
    return project_root() / "params.json"
