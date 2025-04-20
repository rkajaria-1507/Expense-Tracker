import streamlit as st
import sqlite3
import pandas as pd
from category import CategoryManager
from logs import LogManager

def show_category_management():
    # Check if user has admin privileges
    if st.session_state.role != "admin":
        st.error("You don't have permission to access this page.")
        return
        
    st.markdown("<div class='main-header'>Category Management</div>", unsafe_allow_html=True)
    
    # Get database connection and category manager
    conn = sqlite3.connect("ExpenseReport", check_same_thread=False)
    cursor = conn.cursor()
    category_manager = CategoryManager(cursor, conn)
    log_manager = LogManager(cursor, conn)
    log_manager.set_current_user(st.session_state.username)
    
    # Set up tabs for different category operations
    tab1, tab2, tab3 = st.tabs(["List Categories", "Add Category", "Delete Category"])
    
    # List Categories Tab
    with tab1:
        st.subheader("All Categories")
        
        # Query for all categories
        cursor.execute("SELECT category_id, category_name FROM Categories")
        categories = cursor.fetchall()
        
        if categories:
            categories_df = pd.DataFrame(categories, columns=["ID", "Category Name"])
            st.dataframe(categories_df, use_container_width=True)
            
            # Show category usage statistics
            st.subheader("Category Usage")
            cursor.execute("""
                SELECT c.category_name, COUNT(ce.expense_id) as usage_count
                FROM Categories c
                LEFT JOIN category_expense ce ON c.category_id = ce.category_id
                GROUP BY c.category_name
                ORDER BY usage_count DESC
            """)
            usage_data = cursor.fetchall()
            
            if usage_data:
                usage_df = pd.DataFrame(usage_data, columns=["Category", "Usage Count"])
                
                # Create a bar chart for category usage
                st.bar_chart(usage_df.set_index("Category"))
        else:
            st.info("No categories found in the system.")
    
    # Add Category Tab
    with tab2:
        st.subheader("Add New Category")
        
        with st.form("add_category_form"):
            new_category = st.text_input("Category Name")
            submitted = st.form_submit_button("Add Category")
            
            if submitted:
                if not new_category:
                    st.error("Category name cannot be empty.")
                else:
                    # Check if category already exists
                    cursor.execute("SELECT category_id FROM Categories WHERE category_name = ?", (new_category,))
                    if cursor.fetchone():
                        st.error(f"Category '{new_category}' already exists!")
                    else:
                        try:
                            # Add the category
                            result = category_manager.add_category(new_category)
                            if result:
                                log_manager.add_log(log_manager.generate_log_description("add_category", [new_category]))
                                st.success(f"Category '{new_category}' added successfully!")
                        except Exception as e:
                            st.error(f"Error adding category: {e}")
    
    # Delete Category Tab
    with tab3:
        st.subheader("Delete Category")
        
        # Get all categories
        cursor.execute("SELECT category_name FROM Categories")
        all_categories = [cat[0] for cat in cursor.fetchall()]
        
        if not all_categories:
            st.info("No categories available to delete.")
        else:
            category_to_delete = st.selectbox("Select Category to Delete", all_categories)
            
            # Check if the category is in use
            cursor.execute("""
                SELECT COUNT(*) as usage_count
                FROM category_expense ce
                JOIN Categories c ON ce.category_id = c.category_id
                WHERE c.category_name = ?
            """, (category_to_delete,))
            
            usage_count = cursor.fetchone()[0]
            
            if usage_count > 0:
                st.warning(f"This category is used in {usage_count} expenses. Deleting it may affect existing data.")
            
            if st.button("Delete Category", key="confirm_delete_category"):
                result = category_manager.delete_category(category_to_delete)
                if result:
                    log_manager.add_log(log_manager.generate_log_description("delete_category", [category_to_delete]))
                    st.success(f"Category '{category_to_delete}' deleted successfully!")