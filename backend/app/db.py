from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import config
from app.models import Base

engine = create_engine(
    config.DATABASE_URL,
    # timeout: SQLite's busy-wait before raising "database is locked" on a concurrent write -
    # default is 0 (fails immediately). A few seconds lets a losing concurrent writer (see the
    # atomic UPDATE ... WHERE answer IS NULL in orchestrator.submit_answer) wait for the winner's
    # transaction to commit and then correctly observe rowcount=0, instead of raising a raw
    # OperationalError before it ever gets to check.
    connect_args={"check_same_thread": False, "timeout": 10},
)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_session() -> Session:
    return SessionLocal()
