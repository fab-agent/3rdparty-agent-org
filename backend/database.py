from sqlmodel import create_engine, Session, SQLModel
from contextlib import contextmanager
from typing import Generator
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


def _is_fresh_db() -> bool:
    """Return True if the database has no alembic_version table (brand-new install)."""
    from sqlalchemy import inspect, text
    with engine.connect() as conn:
        try:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'"))
            return result.fetchone() is None
        except Exception:
            return True


def init_db() -> None:
    os.makedirs("data", exist_ok=True)

    from alembic.config import Config
    from alembic import command
    ini_path = os.path.join(os.path.dirname(__file__), "alembic.ini")
    alembic_cfg = Config(ini_path)

    if _is_fresh_db():
        # Brand-new database: create all tables directly from SQLModel metadata,
        # then stamp alembic_version to the current head so incremental migrations
        # don't try to add columns to tables that already have them.
        import models  # noqa: F401 — ensure all SQLModel tables are registered
        SQLModel.metadata.create_all(engine)
        command.stamp(alembic_cfg, "head")
    else:
        # Existing database: run only the incremental migrations that are missing.
        command.upgrade(alembic_cfg, "head")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    with Session(engine, expire_on_commit=False) as session:
        yield session
