"""
Configuration settings for Streamlit Cloud deployment
"""
import os
import tempfile

# Database configuration for cloud deployment
DB_CONFIG = {
    "sqlite_path": os.path.join("/tmp", "expense_tracker.db"),
    "demo_data_enabled": True,  # Set to False if you don't want demo data loaded
    "connection_timeout": 30,  # SQLite connection timeout in seconds
    "busy_timeout": 30000,  # SQLite busy timeout in milliseconds
}

# File storage configuration
FILE_CONFIG = {
    "temp_dir": "/tmp",  # Temporary directory for file storage
    "upload_dir": "/tmp/uploads",  # Directory for uploaded files
    "max_upload_size": 10 * 1024 * 1024,  # 10 MB max upload size
    "allowed_extensions": [".csv", ".xlsx", ".xls"]  # Allowed file extensions
}

# Detect if running on Streamlit Cloud
def is_streamlit_cloud():
    """Check if the application is running on Streamlit Cloud"""
    return (os.environ.get('STREAMLIT_SHARING') is not None or 
            os.environ.get('STREAMLIT_CLOUD') is not None)