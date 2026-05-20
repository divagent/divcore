from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from app.config import get_settings_singleton

settings = get_settings_singleton()

# convert async url → sync url
SYNC_DATABASE_URL = settings.DIV_SYNC

engine_sync = create_engine(
    SYNC_DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine_sync,
    autocommit=False,
    autoflush=False,
)


def get_db_sync():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@contextmanager
def get_db_sync_contextmanager():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
