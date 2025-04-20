import streamlit as st
import sqlite3
import pandas as pd
from logs import LogManager
from datetime import datetime

def show_system_logs():
    # Check if user has admin privileges
    if st.session_state.role != "admin":
        st.error("You don't have permission to access this page.")
        return
        
    st.markdown("<div class='main-header'>System Logs</div>", unsafe_allow_html=True)
    
    # Get database connection and log manager
    conn = sqlite3.connect("ExpenseReport", check_same_thread=False)
    cursor = conn.cursor()
    log_manager = LogManager(cursor, conn)
    log_manager.set_current_user(st.session_state.username)
    
    # Add log filtering options
    st.subheader("Filter Logs")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cursor.execute("SELECT DISTINCT username FROM Logs")
        usernames = [row[0] for row in cursor.fetchall()]
        username_filter = st.selectbox("User", ["All Users"] + usernames)
    
    with col2:
        cursor.execute("SELECT DISTINCT description FROM Logs")
        descriptions = [row[0] for row in cursor.fetchall()]
        action_filter = st.selectbox("Action Description", ["All Actions"] + descriptions)
    
    with col3:
        date_range = st.date_input("Date Range", value=[])
    
    limit = st.slider("Maximum entries", min_value=10, max_value=500, value=100, step=10)
    
    query = "SELECT logid, username, description, timestamp FROM Logs WHERE 1=1"
    params = []
    
    if username_filter != "All Users":
        query += " AND username = ?"
        params.append(username_filter)
    
    if action_filter != "All Actions":
        query += " AND description = ?"
        params.append(action_filter)
    
    if date_range:
        if len(date_range) == 2:
            start_date, end_date = date_range
            query += " AND DATE(timestamp) >= ? AND DATE(timestamp) <= ?"
            params.extend([start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")])
        elif len(date_range) == 1:
            single_date = date_range[0]
            query += " AND DATE(timestamp) = ?"
            params.append(single_date.strftime("%Y-%m-%d"))
    
    query += " ORDER BY timestamp DESC"
    
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query, params)
    logs = cursor.fetchall()
    
    if logs:
        st.subheader(f"System Logs ({len(logs)} entries)")
        
        logs_df = pd.DataFrame(logs, columns=["ID", "Username", "Description", "Timestamp"])
        
        st.dataframe(logs_df, use_container_width=True)
        
        if st.button("Export Logs to CSV"):
            logs_df.to_csv("system_logs_export.csv", index=False)
            st.success("Logs exported to system_logs_export.csv")
            log_manager.add_log(log_manager.generate_log_description("export_logs"))
    else:
        st.info("No logs found matching your filters.")
    
    # Add log statistics
    st.subheader("Log Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cursor.execute("""
            SELECT username, COUNT(*) as activity_count 
            FROM Logs 
            GROUP BY username 
            ORDER BY activity_count DESC
        """)
        user_activity = cursor.fetchall()
        
        if user_activity:
            user_df = pd.DataFrame(user_activity, columns=["Username", "Activity Count"])
            st.bar_chart(user_df.set_index("Username"))
            st.caption("User Activity")
    
    with col2:
        cursor.execute("""
            SELECT description, COUNT(*) as description_count 
            FROM Logs 
            GROUP BY description 
            ORDER BY description_count DESC
        """)
        description_counts = cursor.fetchall()
        
        if description_counts:
            description_df = pd.DataFrame(description_counts, columns=["Description", "Count"])
            st.bar_chart(description_df.set_index("Description"))
            st.caption("Action Description Distribution")
    
    cursor.execute("SELECT COUNT(*) FROM Logs")
    total_logs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT username) FROM Logs")
    active_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT MAX(timestamp) FROM Logs")
    last_activity = cursor.fetchone()[0]
    
    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Log Entries", total_logs)
    col2.metric("Active Users", active_users)
    col3.metric("Last Activity", last_activity.split()[0] if last_activity else "N/A")
