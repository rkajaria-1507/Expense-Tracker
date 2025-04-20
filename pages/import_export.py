import streamlit as st
import sqlite3
import pandas as pd
import os
import csv
from csv_operations import CSVOperations
from logs import LogManager
import io

def show_import_export():
    st.markdown("<div class='main-header'>Import/Export Data</div>", unsafe_allow_html=True)
    
    # Get database connection and csv operations manager
    conn = sqlite3.connect("ExpenseReport", check_same_thread=False)
    cursor = conn.cursor()
    csv_operations = CSVOperations(cursor, conn)
    csv_operations.set_current_user(st.session_state.username)
    log_manager = LogManager(cursor, conn)
    log_manager.set_current_user(st.session_state.username)
    
    # Create tabs for import and export
    tab1, tab2 = st.tabs(["Import Expenses", "Export Expenses"])
    
    # Import Tab
    with tab1:
        st.subheader("Import Expenses from CSV")
        
        # Show the expected CSV format
        with st.expander("CSV Format Information"):
            st.markdown("""
            ### CSV Format
            
            Your CSV file should have the following columns:
            
            ```
            amount,category,payment_method,date,description,tag,payment_detail_identifier
            ```
            
            **Example row:**
            ```
            45.99,groceries,credit_card,2023-07-15,Weekly shopping,food,1234
            ```
            
            **Notes:**
            - Date must be in YYYY-MM-DD format
            - Categories and payment methods must already exist in the system
            - The payment_detail_identifier is optional
            """)
            
            # Provide a template download
            template_data = pd.read_csv("import_expenses_template.csv") if os.path.exists("import_expenses_template.csv") else pd.DataFrame(columns=[
                "amount", "category", "payment_method", "date", "description", "tag", "payment_detail_identifier"
            ])
            
            csv_template = template_data.to_csv(index=False)
            st.download_button(
                "Download CSV Template",
                csv_template,
                "import_expenses_template.csv",
                "text/csv",
                key="download_template"
            )
        
        # Upload CSV file
        uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
        
        if uploaded_file is not None:
            # Save the uploaded file temporarily
            with open("temp_import.csv", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Preview the uploaded data
            df = pd.read_csv("temp_import.csv")
            
            st.write("Preview of uploaded data:")
            st.dataframe(df.head(5), use_container_width=True)
            
            # Show validation results
            valid = True
            validation_messages = []
            
            # Check for required columns
            required_columns = ["amount", "category", "payment_method", "date", "description", "tag"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                valid = False
                validation_messages.append(f"❌ Missing required columns: {', '.join(missing_columns)}")
            
            # Check for date format
            if "date" in df.columns:
                try:
                    pd.to_datetime(df["date"], format="%Y-%m-%d")
                except:
                    valid = False
                    validation_messages.append("❌ Date format incorrect. Must be YYYY-MM-DD.")
            
            # Check if categories exist
            if "category" in df.columns:
                cursor.execute("SELECT category_name FROM Categories")
                existing_categories = [cat[0] for cat in cursor.fetchall()]
                unknown_categories = [cat for cat in df["category"].unique() if cat not in existing_categories]
                
                if unknown_categories:
                    valid = False
                    validation_messages.append(f"❌ Unknown categories: {', '.join(unknown_categories)}")
            
            # Check if payment methods exist
            if "payment_method" in df.columns:
                cursor.execute("SELECT payment_method_name FROM Payment_Method")
                existing_methods = [pm[0] for pm in cursor.fetchall()]
                unknown_methods = [pm for pm in df["payment_method"].unique() if pm not in existing_methods]
                
                if unknown_methods:
                    valid = False
                    validation_messages.append(f"❌ Unknown payment methods: {', '.join(unknown_methods)}")
            
            # Display validation messages
            if valid:
                st.success("✓ CSV data is valid and ready to import.")
            else:
                for msg in validation_messages:
                    st.warning(msg)
            
            # Import button (only enabled if valid)
            import_btn = st.button("Import Expenses", disabled=not valid)
            
            if import_btn:
                try:
                    result = csv_operations.import_expenses("temp_import.csv")
                    if result:
                        log_manager.add_log(log_manager.generate_log_description("import_expenses", ["temp_import.csv"]))
                        st.success(f"✓ Successfully imported {len(df)} expenses!")
                        
                        # Clean up temp file
                        if os.path.exists("temp_import.csv"):
                            os.remove("temp_import.csv")
                except Exception as e:
                    st.error(f"Error importing expenses: {str(e)}")
    
    # Export Tab
    with tab2:
        st.subheader("Export Expenses to CSV")
        
        # Allow sorting options
        col1, col2 = st.columns(2)
        
        with col1:
            include_sorting = st.checkbox("Sort data")
        
        with col2:
            if include_sorting:
                sort_field = st.selectbox(
                    "Sort by", 
                    ["date", "amount", "category", "payment_method", "tag"]
                )
            else:
                sort_field = None
        
        # Export options based on user role
        if st.session_state.role == "admin":
            export_option = st.radio(
                "Export scope",
                ["All Users", "Specific User"],
                horizontal=True
            )
            
            if export_option == "Specific User":
                cursor.execute("SELECT username FROM User")
                users = [user[0] for user in cursor.fetchall()]
                selected_user = st.selectbox("Select User", users)
                
                if st.button("Export User's Expenses"):
                    # Build export for specific user
                    query = """
                        SELECT 
                            e.amount, c.category_name, pm.payment_method_name, 
                            e.date, e.description, t.tag_name, pme.payment_detail_identifier
                        FROM Expense e
                        LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                        LEFT JOIN Categories c ON ce.category_id = c.category_id
                        LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
                        LEFT JOIN Tags t ON te.tag_id = t.tag_id
                        LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
                        LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                        LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
                        WHERE ue.username = ?
                    """
                    
                    if sort_field:
                        if sort_field == "date":
                            query += " ORDER BY e.date"
                        elif sort_field == "amount":
                            query += " ORDER BY e.amount"
                        elif sort_field == "category":
                            query += " ORDER BY c.category_name"
                        elif sort_field == "payment_method":
                            query += " ORDER BY pm.payment_method_name"
                        elif sort_field == "tag":
                            query += " ORDER BY t.tag_name"
                    
                    cursor.execute(query, [selected_user])
                    expenses = cursor.fetchall()
                    
                    if expenses:
                        df = pd.DataFrame(expenses, columns=[
                            "amount", "category", "payment_method", 
                            "date", "description", "tag", "payment_detail_identifier"
                        ])
                        
                        # Generate CSV string
                        csv_string = df.to_csv(index=False)
                        
                        # Offer download button
                        file_name = f"{selected_user}_expenses.csv"
                        st.download_button(
                            "Download CSV",
                            csv_string,
                            file_name,
                            "text/csv",
                            key="download_user_csv"
                        )
                        
                        log_manager.add_log(log_manager.generate_log_description("export_csv", [file_name]))
                    else:
                        st.info(f"No expenses found for user {selected_user}.")
            else:
                if st.button("Export All Expenses"):
                    # Build export for all users
                    query = """
                        SELECT 
                            e.amount, c.category_name, pm.payment_method_name, 
                            e.date, e.description, t.tag_name, pme.payment_detail_identifier,
                            ue.username
                        FROM Expense e
                        LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                        LEFT JOIN Categories c ON ce.category_id = c.category_id
                        LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
                        LEFT JOIN Tags t ON te.tag_id = t.tag_id
                        LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
                        LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                        LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
                    """
                    
                    if sort_field:
                        if sort_field == "date":
                            query += " ORDER BY e.date"
                        elif sort_field == "amount":
                            query += " ORDER BY e.amount"
                        elif sort_field == "category":
                            query += " ORDER BY c.category_name"
                        elif sort_field == "payment_method":
                            query += " ORDER BY pm.payment_method_name"
                        elif sort_field == "tag":
                            query += " ORDER BY t.tag_name"
                    
                    cursor.execute(query)
                    expenses = cursor.fetchall()
                    
                    if expenses:
                        df = pd.DataFrame(expenses, columns=[
                            "amount", "category", "payment_method", 
                            "date", "description", "tag", "payment_detail_identifier",
                            "username"
                        ])
                        
                        # Generate CSV string
                        csv_string = df.to_csv(index=False)
                        
                        # Offer download button
                        file_name = "all_expenses.csv"
                        st.download_button(
                            "Download CSV",
                            csv_string,
                            file_name,
                            "text/csv",
                            key="download_all_csv"
                        )
                        
                        log_manager.add_log(log_manager.generate_log_description("export_csv", [file_name]))
                    else:
                        st.info("No expenses found in the system.")
        else:
            # Regular user export
            if st.button("Export My Expenses"):
                # Build export for current user
                query = """
                    SELECT 
                        e.amount, c.category_name, pm.payment_method_name, 
                        e.date, e.description, t.tag_name, pme.payment_detail_identifier
                    FROM Expense e
                    LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                    LEFT JOIN Categories c ON ce.category_id = c.category_id
                    LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
                    LEFT JOIN Tags t ON te.tag_id = t.tag_id
                    LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
                    LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                    LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
                    WHERE ue.username = ?
                """
                
                if sort_field:
                    if sort_field == "date":
                        query += " ORDER BY e.date"
                    elif sort_field == "amount":
                        query += " ORDER BY e.amount"
                    elif sort_field == "category":
                        query += " ORDER BY c.category_name"
                    elif sort_field == "payment_method":
                        query += " ORDER BY pm.payment_method_name"
                    elif sort_field == "tag":
                        query += " ORDER BY t.tag_name"
                
                cursor.execute(query, [st.session_state.username])
                expenses = cursor.fetchall()
                
                if expenses:
                    df = pd.DataFrame(expenses, columns=[
                        "amount", "category", "payment_method", 
                        "date", "description", "tag", "payment_detail_identifier"
                    ])
                    
                    # Generate CSV string
                    csv_string = df.to_csv(index=False)
                    
                    # Offer download button
                    file_name = f"{st.session_state.username}_expenses.csv"
                    st.download_button(
                        "Download CSV",
                        csv_string,
                        file_name,
                        "text/csv",
                        key="download_user_csv"
                    )
                    
                    log_manager.add_log(log_manager.generate_log_description("export_csv", [file_name]))
                else:
                    st.info("You don't have any expenses to export.")
    
    # Data management tips
    with st.expander("Data Management Tips"):
        st.markdown("""
        ### Tips for Data Management
        
        **Importing Data:**
        - Make sure all categories and payment methods exist before importing
        - Check your date format matches YYYY-MM-DD
        - Backup your data before large imports
        
        **Exporting Data:**
        - Consider sorting by date for chronological review
        - Export periodically for backup purposes
        - Use category or tag sorting for specific analysis needs
        """)