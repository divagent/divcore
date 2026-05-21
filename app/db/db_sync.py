from sqlalchemy import create_engine
from contextlib import contextmanager

from app.config import get_settings_singleton

settings = get_settings_singleton()

# convert async url -> sync url
SYNC_DATABASE_URL = settings.DIV_ADMIN.replace(
    "postgresql+asyncpg://",
    "postgresql+psycopg2://",
)

engine_sync = create_engine(
    SYNC_DATABASE_URL,
    pool_pre_ping=True,
)

def get_db_sync():
    with engine_sync.begin() as conn:
        yield conn



@contextmanager
def get_db_sync_contextmanager():
    with engine_sync.begin() as conn:
        yield conn
