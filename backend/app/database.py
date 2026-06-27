import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,  # transparently recover dropped MySQL connections
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(retries: int = 30, delay: float = 2.0) -> None:
    """Wait for the database to be reachable, then create all tables.

    MySQL in docker-compose may take a few seconds to accept connections even
    after the container starts, so we retry before giving up.
    """
    # ensure all models are registered on Base before create_all
    from . import models  # noqa: F401

    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError as err:  # database not ready yet
            last_err = err
            print(f"[init_db] database not ready (attempt {attempt}/{retries}), retrying...")
            time.sleep(delay)
    raise RuntimeError(f"Could not connect to the database: {last_err}")
