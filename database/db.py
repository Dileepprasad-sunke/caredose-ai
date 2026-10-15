"""
CareDose AI — Database Connection & Initialization (database/db.py)
Provides persistent SQLite database access with automatic fallback for
cloud/container FUSE filesystems that do not support POSIX byte-range locks.
"""

import os
import shutil
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PERSISTENT_DB_PATH = Path(os.environ.get("CAREDOSE_DB_PATH", str(BASE_DIR / "caredose.db")))
RUNTIME_DB_PATH = Path("/tmp/caredose_runtime.db")
SCHEMA_PATH = BASE_DIR / "models.sql"


def _detect_direct_sqlite_support() -> bool:
    """Test whether the target directory supports direct SQLite POSIX file locking."""
    try:
        conn = sqlite3.connect(str(PERSISTENT_DB_PATH), check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("CREATE TABLE IF NOT EXISTS _healthcheck (id INTEGER);")
        conn.commit()
        conn.close()
        return True
    except sqlite3.OperationalError:
        return False


_DIRECT_SQLITE_SUPPORTED = _detect_direct_sqlite_support()


class SyncedSQLiteConnection:
    """
    Wraps sqlite3.Connection so that if the host filesystem is a FUSE mount,
    all transactions are synced back to `database/caredose.db` on commit/close.
    """

    def __init__(self, raw_conn: sqlite3.Connection, sync_on_write: bool):
        self._conn = raw_conn
        self._sync_on_write = sync_on_write

    def execute(self, *args, **kwargs):
        return self._conn.execute(*args, **kwargs)

    def executescript(self, *args, **kwargs):
        return self._conn.executescript(*args, **kwargs)

    def commit(self):
        self._conn.commit()
        if self._sync_on_write and RUNTIME_DB_PATH.exists():
            PERSISTENT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(RUNTIME_DB_PATH), str(PERSISTENT_DB_PATH))

    def close(self):
        if self._sync_on_write and RUNTIME_DB_PATH.exists():
            try:
                self._conn.commit()
                PERSISTENT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(RUNTIME_DB_PATH), str(PERSISTENT_DB_PATH))
            except Exception:
                pass
        self._conn.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)


def get_connection():
    """Create and return a thread-safe SQLite connection with Row dict access."""
    if _DIRECT_SQLITE_SUPPORTED:
        conn = sqlite3.connect(str(PERSISTENT_DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return SyncedSQLiteConnection(conn, sync_on_write=False)

    # FUSE filesystem fallback: seed runtime DB from persistent file if needed
    if PERSISTENT_DB_PATH.exists() and PERSISTENT_DB_PATH.stat().st_size > 0 and not RUNTIME_DB_PATH.exists():
        shutil.copy2(str(PERSISTENT_DB_PATH), str(RUNTIME_DB_PATH))

    conn = sqlite3.connect(str(RUNTIME_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return SyncedSQLiteConnection(conn, sync_on_write=True)


def init_db() -> None:
    """Initialize all database tables from models.sql if they do not exist."""
    conn = get_connection()
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()
