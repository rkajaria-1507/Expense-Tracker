import os
import sqlite3
from pathlib import Path
import tempfile
from expense_tracker.database.db_init import initialize_database
 
def get_connection():
    """Return a SQLite connection and cursor using SQLITE_PATH or a writable temp file."""
    db_env = os.getenv("SQLITE_PATH")
    if db_env:
        db_path = Path(db_env)
    else:
        # Use OS temp directory for write access (Cloud-safe)
        db_path = Path(tempfile.gettempdir()) / "expense_tracker.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    cursor = conn.cursor()
    initialize_database(conn)
    return conn, cursor