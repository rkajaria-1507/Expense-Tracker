import os
import sqlite3
from pathlib import Path
import tempfile
import streamlit as st
import sys
from expense_tracker.database.db_init import initialize_database

# Import cloud configuration if available
try:
    from expense_tracker.cloud_config import DB_CONFIG, is_streamlit_cloud
except ImportError:
    # Define defaults if cloud_config is not available
    DB_CONFIG = {
        "sqlite_path": None,
        "demo_data_enabled": True,
        "connection_timeout": 30,
        "busy_timeout": 30000,
    }
    
    def is_streamlit_cloud():
        return os.environ.get('STREAMLIT_SHARING') is not None or os.environ.get('STREAMLIT_CLOUD') is not None

_conn = None
_cursor = None

def get_connection():
    """Return a singleton SQLite connection and cursor, initializing database once."""
    global _conn, _cursor
    if _conn and _cursor:
        return _conn, _cursor
        
    # Determine if we're running in Streamlit Cloud
    running_in_cloud = is_streamlit_cloud()
    
    # Establish new connection
    db_env = os.getenv("SQLITE_PATH") or DB_CONFIG.get("sqlite_path")
    if db_env:
        db_path = Path(db_env)
    elif running_in_cloud:
        # In Streamlit Cloud, use a path in the /tmp directory
        db_path = Path("/tmp/expense_tracker.db")
    else:
        db_path = Path(tempfile.gettempdir()) / "expense_tracker.db"
        
    # Ensure directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Log database location for debugging
    print(f"Database path: {db_path}", file=sys.stderr)
    if hasattr(st, 'write'):
        st.session_state['db_path'] = str(db_path)
    
    # Connect to database
    # Get timeout values from config
    timeout = DB_CONFIG.get("connection_timeout", 30)
    busy_timeout = DB_CONFIG.get("busy_timeout", 30000)
    
    _conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=timeout)
    _conn.execute(f"PRAGMA busy_timeout = {busy_timeout}")
    
    # Initialize database schema and defaults once
    initialize_database(_conn)
    _cursor = _conn.cursor()
    return _conn, _cursor