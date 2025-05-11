import streamlit as st
import pandas as pd
from streamlit import session_state
from expense_tracker.utils.logs import LogManager
from expense_tracker.database.sql_queries import PAYMENT_QUERIES

def show_payment_management():
    # Check if user has admin privileges
    if st.session_state.role != "admin":
        st.error("You don't have permission to access this page.")
        return
    st.markdown("<div class='main-header'>Payment Method Management</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["List Payment Methods", "Add Payment Method", "Delete Payment Method"])
    # Retrieve shared managers
    cursor = session_state.cursor
    payment_manager = session_state.payment_manager
    log_manager = session_state.log_manager
    log_manager.set_current_user(session_state.username)
    
    # List Payment Methods Tab
    with tab1:
        st.subheader("All Payment Methods")
        # Fetch all payment methods
        cursor.execute(PAYMENT_QUERIES["list_payment_methods"])
        payment_methods = cursor.fetchall()
        
        if payment_methods:
            methods_df = pd.DataFrame(payment_methods, columns=["Payment Method"])
            methods_df.index = methods_df.index + 1  # Start numbering from 1
            methods_df.index.name = "No."
            st.dataframe(methods_df, use_container_width=True)
        else:
            st.info("No payment methods found in the system.")
    
    # Add Payment Method Tab
    with tab2:
        st.subheader("Add New Payment Method")
        
        with st.form("add_payment_method_form"):
            new_payment_method = st.text_input("Payment Method Name")
            submit_button = st.form_submit_button("Add Payment Method")
            
            if submit_button:
                if not new_payment_method:
                    st.error("Payment method name cannot be empty.")
                else:
                    result = payment_manager.add_payment_method(new_payment_method)
                    if result:
                        log_manager.add_log(log_manager.generate_log_description("add_payment_method", [new_payment_method]))
                        st.success(f"Payment method '{new_payment_method}' added successfully!")
                    else:
                        st.error(f"Failed to add payment method '{new_payment_method}'. It may already exist.")
    # Delete Payment Method Tab
    with tab3:
        st.subheader("Delete Payment Method")
        # Fetch payment methods for deletion
        cursor.execute(PAYMENT_QUERIES["list_payment_methods"])
        methods_to_delete = [m[0] for m in cursor.fetchall()]
        if not methods_to_delete:
            st.info("No payment methods available to delete.")
        else:
            method = st.selectbox("Select Payment Method to Delete", methods_to_delete)
            # Count associated expenses
            cursor.execute(PAYMENT_QUERIES["check_payment_expenses"], (method,))
            expense_count = cursor.fetchone()[0]
            st.warning(f"Deleting payment method '{method}' will remove it and {expense_count} associated expenses. This action cannot be undone.")
            # Confirmation before deletion
            confirm = st.checkbox("I understand the consequences and want to delete this payment method", key="confirm_payment_delete")
            if confirm and st.button("Delete Payment Method", key="delete_payment_btn"):
                result = payment_manager.delete_payment_method(method)
                if result:
                    log_manager.add_log(log_manager.generate_log_description("delete_payment_method", [method]))
                    st.success(f"Payment method '{method}' deleted successfully!")
                else:
                    st.error(f"Failed to delete payment method '{method}'.")