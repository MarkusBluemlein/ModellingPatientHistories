import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

def load_env(root: Path | None = None, env_filename: str = ".env") -> None:
    root = root or Path(__file__).resolve().parents[2]
    env_path = root / env_filename
    load_dotenv(env_path)

def get_engine() -> Engine:
    load_env()
    url = os.getenv("DATABASE_URL")
    if not url:
        host = os.getenv("PGHOST", "localhost")
        port = os.getenv("PGPORT", "5432")
        db   = os.getenv("PGDATABASE")
        user = os.getenv("PGUSER")
        pwd  = os.getenv("PGPASSWORD")
        if not all([db, user, pwd]):
            raise RuntimeError("PGDATABASE/PGUSER/PGPASSWORD fehlen in .env")
        url = f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{db}"
    return create_engine(url, pool_pre_ping=True)
