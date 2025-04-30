import os
import sqlite3
import shutil
from pathlib import Path
from expense_tracker.database.db_init import initialize_database

# Determine project root (two levels up from this file)
project_root = Path(__file__).resolve().parent.parent.parent

def get_connection():
    """Return a SQLite connection and cursor based on SQLITE_PATH env var or default path."""
    # Env var override
    db_env = os.getenv("SQLITE_PATH")
    if db_env:
        db_path = Path(db_env)
    else:
        db_path = project_root / "expense_tracker" / "database" / "ExpenseReport"
        # Copy bundled DB if missing
        if not db_path.exists() and (project_root / "ExpenseReport").exists():
            shutil.copy(project_root / "ExpenseReport", db_path)
    # Ensure directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # Connect
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    cursor = conn.cursor()
    # Initialize tables if not present
    initialize_database(conn)
    return conn, cursor