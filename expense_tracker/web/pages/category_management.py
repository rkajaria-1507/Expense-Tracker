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
from expense_tracker.core.category import CategoryManager
from expense_tracker.utils.logs import LogManager

def show_category_management():
    # Check if user has admin privileges
    if st.session_state.role != "admin":
        st.error("You don't have permission to access this page.")
        return
        
    st.markdown("<div class='main-header'>Category Management</div>", unsafe_allow_html=True)
    
    # Setup tabs for different category management functions
    tab1, tab2, tab3 = st.tabs(["List Categories", "Add Category", "Delete Category"])
    
    # Get database connection and category manager
    # Reuse existing connection if in st.session_state
    if "conn" in st.session_state and "cursor" in st.session_state:
        conn = st.session_state.conn
        cursor = st.session_state.cursor
    else:
        db_path = os.path.join(project_root, "expense_tracker", "database", "ExpenseReport")
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = conn.cursor()
    
    category_manager = CategoryManager(cursor, conn)
    log_manager = LogManager(cursor, conn)
    log_manager.set_current_user(st.session_state.username)
    
    # List Categories Tab
    with tab1:
        st.subheader("All Categories")
        
        # Query to get all categories
        cursor.execute("SELECT category_name FROM Categories ORDER BY category_name")
        categories = cursor.fetchall()
        
        if categories:
            categories_df = pd.DataFrame(categories, columns=["Category Name"])
            categories_df.index = categories_df.index + 1  # Start numbering from 1
            categories_df.index.name = "No."
            st.dataframe(categories_df, use_container_width=True)
        else:
            st.info("No categories found in the system.")
    
    # Add Category Tab
    with tab2:
        st.subheader("Add New Category")
        
        with st.form("add_category_form"):
            new_category = st.text_input("Category Name")
            submit_button = st.form_submit_button("Add Category")
            
            if submit_button:
                if not new_category:
                    st.error("Category name cannot be empty.")
                else:
                    result = category_manager.add_category(new_category)
                    if result:
                        log_manager.add_log(log_manager.generate_log_description("add_category", [new_category]))
                        st.success(f"Category '{new_category}' added successfully!")
                    else:
                        st.error(f"Failed to add category '{new_category}'. It may already exist.")
    
    # Delete Category Tab
    with tab3:
        st.subheader("Delete Category")
        
        # Get list of categories for deletion
        cursor.execute("SELECT category_name FROM Categories ORDER BY category_name")
        categories_to_delete = [cat[0] for cat in cursor.fetchall()]
        
        if not categories_to_delete:
            st.info("No categories available to delete.")
        else:
            category_to_delete = st.selectbox("Select Category to Delete", categories_to_delete)
            
            # Get category expense count
            cursor.execute("""
                SELECT COUNT(*) 
                FROM category_expense ce
                JOIN Categories c ON ce.category_id = c.category_id
                WHERE c.category_name = ?
            """, (category_to_delete,))
            
            expense_count = cursor.fetchone()[0]
            
            # Display category information and warning
            st.markdown(f"**Category:** {category_to_delete}")
            
            # Warning about deletion of all related data
            st.warning(f"Deleting this category will remove it and all associated {expense_count} expenses. This action cannot be undone.")
            
            # Confirmation before deletion
            delete_confirm = st.checkbox("I understand the consequences and want to delete this category", key="confirm_cat_delete")
            if delete_confirm:
                if st.button("Delete Category", key="delete_category_btn"):
                    result = category_manager.delete_category(category_to_delete)
                    if result:
                        log_manager.add_log(log_manager.generate_log_description("delete_category", [category_to_delete]))
                        st.success(f"Category '{category_to_delete}' deleted successfully!")
                    else:
                        st.error(f"Failed to delete category '{category_to_delete}'.")