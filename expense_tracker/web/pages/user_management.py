import streamlit as st
import sqlite3
import pandas as pd
import os
import sys

# Get project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Updated imports from the package structure
from expense_tracker.core.user import UserManager
from expense_tracker.utils.logs import LogManager

def show_user_management():
    # Check if user has admin privileges
    if st.session_state.role != "admin":
        st.error("You don't have permission to access this page.")
        return
        
    st.markdown("<div class='main-header'>User Management</div>", unsafe_allow_html=True)
    
    # Setup tabs for different user management functions
    tab1, tab2, tab3 = st.tabs(["List Users", "Add User", "Delete User"])
    
    # Get database connection and user manager
    # Reuse existing connection if in st.session_state
    if "conn" in st.session_state and "cursor" in st.session_state:
        conn = st.session_state.conn
        cursor = st.session_state.cursor
    else:
        db_path = os.path.join(project_root, "expense_tracker", "database", "ExpenseReport")
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = conn.cursor()
    
    user_manager = UserManager(cursor, conn)
    user_manager.current_user = st.session_state.username
    user_manager.privileges = st.session_state.role
    
    log_manager = LogManager(cursor, conn)
    log_manager.set_current_user(st.session_state.username)
    
    # List Users Tab
    with tab1:
        st.subheader("All Users")
        
        # Query to get all users and their roles
        cursor.execute("""
            SELECT u.username, r.role_name
            FROM User u
            JOIN user_role ur ON u.username = ur.username
            JOIN Role r ON ur.role_id = r.role_id
        """)
        users = cursor.fetchall()
        
        if users:
            users_df = pd.DataFrame(users, columns=["Username", "Role"])
            users_df.index = users_df.index + 1  # Start numbering from 1
            users_df.index.name = "No."
            st.dataframe(users_df, use_container_width=True)
        else:
            st.info("No users found in the system.")
    
    # Add User Tab
    with tab2:
        st.subheader("Add New User")
        
        with st.form("add_user_form"):
            new_username = st.text_input("Username", key="new_username")
            new_password = st.text_input("Password", type="password", key="new_password")
            new_role = st.selectbox("Role", ["admin", "user"], key="new_role")
            
            submit_button = st.form_submit_button("Add User")
            
            if submit_button:
                # Attempt to register new user and get error message if any
                success, message = user_manager.register(new_username, new_password, new_role)
                if success:
                    log_manager.add_log(log_manager.generate_log_description("register", [new_username, new_role]))
                    st.success(f"User '{new_username}' with role '{new_role}' added successfully!")
                else:
                    st.error(message or "Failed to add user.")
    
    # Delete User Tab
    with tab3:
        st.subheader("Delete User")
        
        # Get list of users except the current admin
        cursor.execute("""
            SELECT u.username
            FROM User u
            JOIN user_role ur ON u.username = ur.username
            JOIN Role r ON ur.role_id = r.role_id
            WHERE u.username != ?
        """, (st.session_state.username,))
        
        users_to_delete = [user[0] for user in cursor.fetchall()]
        
        if not users_to_delete:
            st.info("No other users to delete.")
        else:
            user_to_delete = st.selectbox("Select User to Delete", users_to_delete)
            
            # Get user details
            cursor.execute("""
                SELECT r.role_name
                FROM User u
                JOIN user_role ur ON u.username = ur.username
                JOIN Role r ON ur.role_id = r.role_id
                WHERE u.username = ?
            """, (user_to_delete,))
            
            # Store the result of fetchone() in a variable first
            result = cursor.fetchone()
            if result and len(result) > 0:
                user_role = result[0]
            else:
                user_role = "Unknown"

            # Get user expense count
            cursor.execute("""
                SELECT COUNT(*)
                FROM user_expense
                WHERE username = ?
            """, (user_to_delete,))
                
            result = cursor.fetchone()
            if result is not None and len(result) > 0:
                expense_count = result[0]
            else:
                expense_count = 0

            # Display user information and warning
            st.markdown(f"**Username:** {user_to_delete}")
            st.markdown(f"**Role:** {user_role}")
            
            # Warning about deletion of all related user data
            st.warning(f"Deleting user '{user_to_delete}' will remove the user and all associated data, including {expense_count} expenses. This action cannot be undone.")
            # Confirmation before deletion
            delete_confirm = st.checkbox("I understand the consequences and want to delete this user", key="confirm_user_delete")
            if delete_confirm and st.button("Delete User", key="delete_user_btn"):
                result = user_manager.delete_user(user_to_delete)
                if result:
                    log_manager.add_log(log_manager.generate_log_description("delete_user", [user_to_delete]))
                    st.success(f"User '{user_to_delete}' deleted successfully!")
                else:
                    st.error(f"Failed to delete user '{user_to_delete}'.")