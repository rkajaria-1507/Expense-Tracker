import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import sys

# Get project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Updated imports from the package structure
from expense_tracker.core.expense import ExpenseManager
from expense_tracker.utils.logs import LogManager

def show_manage_expenses():
    st.markdown("<div class='main-header'>Expense Management</div>", unsafe_allow_html=True)
    
    # Get database connection and expense manager using same path as app.py
    db_path = os.path.join(project_root, "expense_tracker", "database", "ExpenseReport")
    # Reuse existing connection if in st.session_state
    if "conn" in st.session_state and "cursor" in st.session_state:
        conn = st.session_state.conn
        cursor = st.session_state.cursor
    else:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = conn.cursor()
    
    expense_manager = ExpenseManager(cursor, conn)
    expense_manager.set_current_user(st.session_state.username)
    log_manager = LogManager(cursor, conn)
    log_manager.set_current_user(st.session_state.username)
    
    # Rest of the code remains the same
    # Set up tabs for different expense operations
    tab1, tab2, tab3, tab4 = st.tabs(["Add Expense", "List Expenses", "Update Expense", "Delete Expense"])
    
    # Add Expense Tab
    with tab1:
        st.subheader("Add New Expense")
        
        # Get available categories
        cursor.execute("SELECT category_name FROM Categories")
        categories = [cat[0] for cat in cursor.fetchall()]
        
        # Get available payment methods
        cursor.execute("SELECT payment_method_name FROM Payment_Method")
        payment_methods = [pm[0] for pm in cursor.fetchall()]
        
        if not categories or not payment_methods:
            st.warning("Please make sure categories and payment methods are available before adding expenses.")
        else:
            with st.form("add_expense_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    amount = st.number_input("Amount", min_value=0.01, format="%.2f")
                    category = st.selectbox("Category", categories)
                    payment_method = st.selectbox("Payment Method", payment_methods)
                
                with col2:
                    date = st.date_input("Date")
                    tag = st.text_input("Tag", value="general")
                    payment_detail = st.text_input("Payment Detail (optional)", 
                                                help="e.g., last 4 digits of card, account info, etc.")
                
                description = st.text_area("Description")
                
                submitted = st.form_submit_button("Add Expense")
                
                if submitted:
                    # Format date as string (YYYY-MM-DD)
                    date_str = date.strftime("%Y-%m-%d")
                    
                    # Validate input
                    if amount <= 0:
                        st.error("Amount must be greater than zero.")
                    elif not description:
                        st.error("Description cannot be empty.")
                    else:
                        # Add expense
                        result = expense_manager.addexpense(
                            amount, category, payment_method, date_str, 
                            description, tag, payment_detail
                        )
                        
                        if result:
                            log_manager.add_log(log_manager.generate_log_description("add_expense"))
                            st.success("Expense added successfully!")
    
    # List Expenses Tab
    with tab2:
        st.subheader("Expense List")
        
        # Add filtering options
        with st.expander("Filter Expenses"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Date range filter
                start_date = st.date_input("Start Date", value=None)
                end_date = st.date_input("End Date", value=None)
                
                # Amount range filter
                min_amount = st.number_input("Min Amount", value=0.0, format="%.2f")
                max_amount = st.number_input("Max Amount", value=None, format="%.2f")
            
            with col2:
                # Category filter
                cursor.execute("SELECT category_name FROM Categories")
                all_categories = [cat[0] for cat in cursor.fetchall()]
                selected_category = st.selectbox("Category", ["All"] + all_categories)
                
                # Payment method filter
                cursor.execute("SELECT payment_method_name FROM Payment_Method")
                all_methods = [pm[0] for pm in cursor.fetchall()]
                selected_method = st.selectbox("Payment Method", ["All"] + all_methods)
                
                # Tag filter
                cursor.execute("SELECT DISTINCT tag_name FROM Tags")
                all_tags = [tag[0] for tag in cursor.fetchall()]
                selected_tag = st.selectbox("Tag", ["All"] + all_tags)
        
        # Build the query based on filters
        query = """
            SELECT e.expense_id, e.date, e.amount, e.description, 
                c.category_name, t.tag_name, pm.payment_method_name
            FROM Expense e
            LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
            LEFT JOIN Categories c ON ce.category_id = c.category_id
            LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
            LEFT JOIN Tags t ON te.tag_id = t.tag_id
            LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
            LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
            LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
            WHERE 1=1
        """
        params = []
        
        # Add filters to the query
        if st.session_state.role != "admin":
            # Regular users can only see their own expenses
            query += " AND ue.username = ?"
            params.append(st.session_state.username)
        
        if start_date:
            query += " AND e.date >= ?"
            params.append(start_date.strftime("%Y-%m-%d"))
        
        if end_date:
            query += " AND e.date <= ?"
            params.append(end_date.strftime("%Y-%m-%d"))
        
        if min_amount > 0:
            query += " AND e.amount >= ?"
            params.append(min_amount)
        
        if max_amount and max_amount > 0:
            query += " AND e.amount <= ?"
            params.append(max_amount)
        
        if selected_category != "All":
            query += " AND c.category_name = ?"
            params.append(selected_category)
        
        if selected_method != "All":
            query += " AND pm.payment_method_name = ?"
            params.append(selected_method)
        
        if selected_tag != "All":
            query += " AND t.tag_name = ?"
            params.append(selected_tag)
        
        query += " ORDER BY e.date DESC"
        
        # Execute the query
        cursor.execute(query, params)
        expenses = cursor.fetchall()
        
        if expenses:
            # Convert to DataFrame for display
            df = pd.DataFrame(expenses, columns=[
                "ID", "Date", "Amount", "Description", "Category", "Tag", "Payment Method"
            ])
            st.dataframe(df, use_container_width=True)
            
            # Summary information
            st.markdown(f"**Total: ${df['Amount'].sum():.2f}** ({len(df)} expenses)")
        else:
            st.info("No expenses found matching your filters.")
    
    # Update Expense Tab
    with tab3:
        st.subheader("Update Expense")
        
        # Get user expenses for selection
        if st.session_state.role == "admin":
            cursor.execute("""
                SELECT e.expense_id, e.date, e.amount, c.category_name, 
                    t.tag_name, pm.payment_method_name, e.description, ue.username
                FROM Expense e
                LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                LEFT JOIN Categories c ON ce.category_id = c.category_id
                LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
                LEFT JOIN Tags t ON te.tag_id = t.tag_id
                LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
                LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
                ORDER BY e.date DESC
            """)
        else:
            cursor.execute("""
                SELECT e.expense_id, e.date, e.amount, c.category_name, 
                    t.tag_name, pm.payment_method_name, e.description
                FROM Expense e
                LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                LEFT JOIN Categories c ON ce.category_id = c.category_id
                LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
                LEFT JOIN Tags t ON te.tag_id = t.tag_id
                LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
                LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
                WHERE ue.username = ?
                ORDER BY e.date DESC
            """, (st.session_state.username,))
        
        expenses = cursor.fetchall()
        
        if not expenses:
            st.info("No expenses available to update.")
        else:
            # Format expenses for selection
            if st.session_state.role == "admin":
                expense_options = [f"ID: {e[0]} | {e[1]} | ${e[2]} | {e[3]} | User: {e[7]}" for e in expenses]
            else:
                expense_options = [f"ID: {e[0]} | {e[1]} | ${e[2]} | {e[3]}" for e in expenses]
            
            selected_expense = st.selectbox("Select Expense to Update", expense_options)
            expense_id = int(selected_expense.split('|')[0].split(':')[1].strip())
            
            # Get available categories and payment methods
            cursor.execute("SELECT category_name FROM Categories")
            categories = [cat[0] for cat in cursor.fetchall()]
            
            cursor.execute("SELECT payment_method_name FROM Payment_Method")
            payment_methods = [pm[0] for pm in cursor.fetchall()]
            
            # Get current expense details for pre-filling the form
            cursor.execute("""
                SELECT e.amount, e.date, e.description, c.category_name, 
                    t.tag_name, pm.payment_method_name, pme.payment_detail_identifier
                FROM Expense e
                LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                LEFT JOIN Categories c ON ce.category_id = c.category_id
                LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
                LEFT JOIN Tags t ON te.tag_id = t.tag_id
                LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
                LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                WHERE e.expense_id = ?
            """, (expense_id,))
            
            expense_details = cursor.fetchone()
            
            if expense_details:
                current_amount, current_date, current_desc, current_category, current_tag, current_method, current_payment_detail = expense_details
                
                st.markdown("**Update Fields:**")
                
                # Create a 3-column layout for field updates
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    field_to_update = st.selectbox(
                        "Select Field to Update",
                        ["amount", "date", "description", "category", "tag", "payment_method"]
                    )
                
                with col2:
                    # Display current value based on selected field
                    if field_to_update == "amount":
                        st.text_input("Current Value", value=str(current_amount), disabled=True)
                    elif field_to_update == "date":
                        st.text_input("Current Value", value=current_date, disabled=True)
                    elif field_to_update == "description":
                        st.text_input("Current Value", value=current_desc, disabled=True)
                    elif field_to_update == "category":
                        st.text_input("Current Value", value=current_category, disabled=True)
                    elif field_to_update == "tag":
                        st.text_input("Current Value", value=current_tag, disabled=True)
                    elif field_to_update == "payment_method":
                        st.text_input("Current Value", value=current_method, disabled=True)
                
                with col3:
                    # Input for new value based on selected field
                    if field_to_update == "amount":
                        new_value = st.number_input("New Amount", value=float(current_amount), format="%.2f")
                    elif field_to_update == "date":
                        new_date = st.date_input("New Date", datetime.strptime(current_date, "%Y-%m-%d").date())
                        new_value = new_date.strftime("%Y-%m-%d")
                    elif field_to_update == "description":
                        new_value = st.text_input("New Description", value=current_desc)
                    elif field_to_update == "category":
                        new_value = st.selectbox("New Category", categories, index=categories.index(current_category) if current_category in categories else 0)
                    elif field_to_update == "tag":
                        new_value = st.text_input("New Tag", value=current_tag)
                    elif field_to_update == "payment_method":
                        new_value = st.selectbox("New Payment Method", payment_methods, index=payment_methods.index(current_method) if current_method in payment_methods else 0)
                
                # Update button
                if st.button("Update Expense", key="update_expense_btn"):
                    if field_to_update in ["amount", "date", "description", "category", "tag", "payment_method"]:
                        result = expense_manager.update_expense(expense_id, field_to_update, str(new_value))
                        if result:
                            log_manager.add_log(log_manager.generate_log_description("update_expense", [str(expense_id), field_to_update]))
                            st.success(f"Expense ID {expense_id} updated successfully!")
    
    # Delete Expense Tab
    with tab4:
        st.subheader("Delete Expense")
        
        # Get user expenses for deletion
        if st.session_state.role == "admin":
            cursor.execute("""
                SELECT e.expense_id, e.date, e.amount, c.category_name, 
                    t.tag_name, pm.payment_method_name, e.description, ue.username
                FROM Expense e
                LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                LEFT JOIN Categories c ON ce.category_id = c.category_id
                LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
                LEFT JOIN Tags t ON te.tag_id = t.tag_id
                LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
                LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
                ORDER BY e.date DESC
            """)
        else:
            cursor.execute("""
                SELECT e.expense_id, e.date, e.amount, c.category_name, 
                    t.tag_name, pm.payment_method_name, e.description
                FROM Expense e
                LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                LEFT JOIN Categories c ON ce.category_id = c.category_id
                LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
                LEFT JOIN Tags t ON te.tag_id = t.tag_id
                LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
                LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
                WHERE ue.username = ?
                ORDER BY e.date DESC
            """, (st.session_state.username,))
        
        expenses = cursor.fetchall()
        
        if not expenses:
            st.info("No expenses available to delete.")
        else:
            # Format expenses for selection
            if st.session_state.role == "admin":
                expense_options = [f"ID: {e[0]} | {e[1]} | ${e[2]} | {e[3]} | User: {e[7]}" for e in expenses]
            else:
                expense_options = [f"ID: {e[0]} | {e[1]} | ${e[2]} | {e[3]}" for e in expenses]
            
            selected_expense = st.selectbox("Select Expense to Delete", expense_options, key="delete_expense_select")
            expense_id = int(selected_expense.split('|')[0].split(':')[1].strip())
            
            # Display expense details
            for expense in expenses:
                if expense[0] == expense_id:
                    st.markdown("**Expense Details:**")
                    
                    details = {
                        "ID": expense[0],
                        "Date": expense[1],
                        "Amount": f"${expense[2]:.2f}",
                        "Category": expense[3],
                        "Tag": expense[4],
                        "Payment Method": expense[5],
                        "Description": expense[6]
                    }
                    
                    if st.session_state.role == "admin":
                        details["User"] = expense[7]
                    
                    for key, value in details.items():
                        st.markdown(f"**{key}:** {value}")
                    
                    break
            
            # Confirmation for deletion
            st.warning("This action cannot be undone. Are you sure you want to delete this expense?")
            
            if st.button("Delete Expense", key="confirm_delete_expense"):
                result = expense_manager.delete_expense(expense_id)
                if result:
                    log_manager.add_log(log_manager.generate_log_description("delete_expense", [str(expense_id)]))
                    st.success(f"Expense ID {expense_id} deleted successfully!")