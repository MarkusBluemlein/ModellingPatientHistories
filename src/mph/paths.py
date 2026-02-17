"""
mph.paths
=========
Zentrale Pfadfunktionen für das Repository "ModellingPatientHistories".
"""

from __future__ import annotations
from pathlib import Path

def project_root() -> Path:
    """Ermittelt das Repo-Root anhand des Ordnernamens 'ModellingPatientHistories'."""
    here = Path(__file__).resolve()
    PROJECT_ROOT = next((p for p in here.parents if p.name == "ModellingPatientHistories"), None)

    if PROJECT_ROOT is None:
        raise RuntimeError(
            f"Unerwarteter Projektroot: {here} (Name ist {here.name}). "
            "Starte das Notebook aus ModellingPatientHistories/notebooks oder passe parents[...] an."
        )

    return PROJECT_ROOT

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
