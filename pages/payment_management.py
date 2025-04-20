import streamlit as st
import sqlite3
import pandas as pd
from payment import PaymentManager
from logs import LogManager

def show_payment_management():
    # Check if user has admin privileges
    if st.session_state.role != "admin":
        st.error("You don't have permission to access this page.")
        return
        
    st.markdown("<div class='main-header'>Payment Method Management</div>", unsafe_allow_html=True)
    
    # Get database connection and payment manager
    conn = sqlite3.connect("ExpenseReport", check_same_thread=False)
    cursor = conn.cursor()
    payment_manager = PaymentManager(cursor, conn)
    log_manager = LogManager(cursor, conn)
    log_manager.set_current_user(st.session_state.username)
    
    # Set up tabs for different payment method operations
    tab1, tab2, tab3 = st.tabs(["List Payment Methods", "Add Payment Method", "Delete Payment Method"])
    
    # List Payment Methods Tab
    with tab1:
        st.subheader("All Payment Methods")
        
        # Query for all payment methods
        cursor.execute("SELECT payment_method_id, payment_method_name FROM Payment_Method")
        payment_methods = cursor.fetchall()
        
        if payment_methods:
            methods_df = pd.DataFrame(payment_methods, columns=["ID", "Payment Method"])
            st.dataframe(methods_df, use_container_width=True)
            
            # Show payment method usage statistics
            st.subheader("Payment Method Usage")
            cursor.execute("""
                SELECT pm.payment_method_name, COUNT(pme.expense_id) as usage_count
                FROM Payment_Method pm
                LEFT JOIN payment_method_expense pme ON pm.payment_method_id = pme.payment_method_id
                GROUP BY pm.payment_method_name
                ORDER BY usage_count DESC
            """)
            usage_data = cursor.fetchall()
            
            if usage_data:
                usage_df = pd.DataFrame(usage_data, columns=["Payment Method", "Usage Count"])
                
                # Create a bar chart for payment method usage
                st.bar_chart(usage_df.set_index("Payment Method"))
        else:
            st.info("No payment methods found in the system.")
    
    # Add Payment Method Tab
    with tab2:
        st.subheader("Add New Payment Method")
        
        with st.form("add_payment_method_form"):
            new_payment_method = st.text_input("Payment Method Name")
            submitted = st.form_submit_button("Add Payment Method")
            
            if submitted:
                if not new_payment_method:
                    st.error("Payment method name cannot be empty.")
                else:
                    # Check if payment method already exists
                    cursor.execute("SELECT payment_method_id FROM Payment_Method WHERE payment_method_name = ?", 
                                (new_payment_method,))
                    if cursor.fetchone():
                        st.error(f"Payment method '{new_payment_method}' already exists!")
                    else:
                        try:
                            # Add the payment method
                            result = payment_manager.add_payment_method(new_payment_method)
                            if result:
                                log_manager.add_log(log_manager.generate_log_description("add_payment_method", [new_payment_method]))
                                st.success(f"Payment method '{new_payment_method}' added successfully!")
                        except Exception as e:
                            st.error(f"Error adding payment method: {e}")
    
    # Delete Payment Method Tab
    with tab3:
        st.subheader("Delete Payment Method")
        
        # Get all payment methods
        cursor.execute("SELECT payment_method_name FROM Payment_Method")
        all_methods = [method[0] for method in cursor.fetchall()]
        
        if not all_methods:
            st.info("No payment methods available to delete.")
        else:
            method_to_delete = st.selectbox("Select Payment Method to Delete", all_methods)
            
            # Check if the payment method is in use
            cursor.execute("""
                SELECT COUNT(*) as usage_count
                FROM payment_method_expense pme
                JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                WHERE pm.payment_method_name = ?
            """, (method_to_delete,))
            
            usage_count = cursor.fetchone()[0]
            
            if usage_count > 0:
                st.warning(f"This payment method is used in {usage_count} expenses. Deleting it may affect existing data.")
            
            if st.button("Delete Payment Method", key="confirm_delete_method"):
                result = payment_manager.delete_payment_method(method_to_delete)
                if result:
                    log_manager.add_log(log_manager.generate_log_description("delete_payment_method", [method_to_delete]))
                    st.success(f"Payment method '{method_to_delete}' deleted successfully!")