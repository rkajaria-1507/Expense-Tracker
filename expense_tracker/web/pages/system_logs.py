import streamlit as st
import pandas as pd
from datetime import datetime
from expense_tracker.database.connection import get_connection
from expense_tracker.utils.logs import LogManager
from expense_tracker.database.sql_queries import LOG_QUERIES

def show_system_logs():
    # Check if user has admin privileges
    if st.session_state.role != "admin":
        st.error("You don't have permission to access this page.")
        return
    
    st.markdown("<div class='main-header'>System Logs</div>", unsafe_allow_html=True)
    
    # Initialize DB connection and manager
    conn, cursor = get_connection()
    
    log_manager = LogManager(cursor, conn)
    
    # Set up filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Get unique usernames from log table
        cursor.execute(LOG_QUERIES["get_users_with_logs"])
        usernames = [row[0] for row in cursor.fetchall()]
        selected_user = st.selectbox("Filter by User", ["All"] + usernames)
    
    with col2:
        # Allow filtering by date range
        start_date = st.date_input("Start Date", value=None)
    
    with col3:
        end_date = st.date_input("End Date", value=None)
    
    # Get log entries with filters
    query = LOG_QUERIES["view_logs_base"]
    params = []
    
    # Add WHERE clause if any filter is applied
    where_clause = " WHERE 1=1"
    query += where_clause
    
    if selected_user != "All":
        query += " AND username = ?"
        params.append(selected_user)
    
    if start_date:
        start_date_str = start_date.strftime("%Y-%m-%d")
        query += " AND date(timestamp) >= ?"
        params.append(start_date_str)
    
    if end_date:
        end_date_str = end_date.strftime("%Y-%m-%d")
        query += " AND date(timestamp) <= ?"
        params.append(end_date_str)
    
    query += LOG_QUERIES["view_logs_order"] + " LIMIT 1000"
    
    cursor.execute(query, params)
    logs = cursor.fetchall()
    
    if logs:
        # Format logs for display
        # Make sure the column names match the number of columns in the data
        column_names = ["ID", "Username", "Activity Type", "Timestamp"]
        if len(logs[0]) == 5:  # If there are 5 columns in the data
            column_names.append("Details")
            
        logs_df = pd.DataFrame(logs, columns=column_names)
        # Start row numbering from 1
        logs_df.index = logs_df.index + 1
        logs_df.index.name = "No."
        
        # Apply formatting - Fix: Safely convert timestamp strings to datetime objects
        def safe_datetime_format(x):
            try:
                if pd.notna(x) and isinstance(x, str):
                    # Try to parse as datetime
                    dt = pd.to_datetime(x, errors='coerce')
                    if pd.notna(dt):
                        return dt.strftime("%Y-%m-%d %H:%M:%S")
                return x  # Return original value if not parseable as datetime
            except:
                return x  # Return original value on any error
                
        logs_df["Timestamp"] = logs_df["Timestamp"].apply(safe_datetime_format)
        
        st.dataframe(logs_df, use_container_width=True)
        
        st.info(f"Showing {len(logs)} most recent log entries. Use filters to narrow down results.")
    else:
        st.info("No log entries found matching the selected filters.")