import os
import sqlite3
from pathlib import Path
import tempfile
from expense_tracker.database.db_init import initialize_database

_conn = None
_cursor = None

def get_connection():
    """Return a singleton SQLite connection and cursor, initializing database once."""
    global _conn, _cursor
    if _conn and _cursor:
        return _conn, _cursor
    # Establish new connection
    db_env = os.getenv("SQLITE_PATH")
    if db_env:
        db_path = Path(db_env)
    else:
        db_path = Path(tempfile.gettempdir()) / "expense_tracker.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    _conn.execute("PRAGMA busy_timeout = 30000")
    # Initialize database schema and defaults once
    initialize_database(_conn)
    _cursor = _conn.cursor()
    return _conn, _cursor