from pathlib import Path

def project_root() -> Path:
    # root liegt 2 Ebenen höher als /src/mph. parents[2] springt 2 Ebenen nach oben
    return Path(__file__).resolve().parents[2]

def data_dir() -> Path:
    return project_root() / "data"

def outcome_dir() -> Path:
    return project_root() / "outputs"
