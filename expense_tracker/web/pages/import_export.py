import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime
from streamlit import session_state
from expense_tracker.utils.csv_operations import CSVOperations
from expense_tracker.utils.logs import LogManager
import os
from pathlib import Path

# Determine project root for static templates
project_root = Path(__file__).resolve().parent.parent.parent

def show_import_export():
    st.markdown("<div class='main-header'>Import/Export Data</div>", unsafe_allow_html=True)
    # Retrieve shared managers and cursor
    cursor = session_state.cursor
    csv_operations = session_state.csv_operations
    log_manager = session_state.log_manager
    csv_operations.set_current_user(session_state.username)
    log_manager.set_current_user(session_state.username)

    # Setup tabs for import and export
    tab1, tab2 = st.tabs(["Import", "Export"])

    # Import Tab
    with tab1:
        st.subheader("Import Expenses from CSV")
        
        # Show template download link
        template_path = project_root / "expense_tracker" / "static" / "templates" / "import_expenses_template.csv"
        
        if os.path.exists(template_path):
            with open(template_path, "r") as f:
                template_content = f.read()
            
            st.download_button(
                label="Download CSV Template",
                data=template_content,
                file_name="expense_template.csv",
                mime="text/csv"
            )
            
            st.markdown("""        
            **CSV Format Requirements:**
            - Headers: amount, category, payment_method, date, description, tag, payment_detail_identifier (optional)
            - Date format: YYYY-MM-DD
            - Categories and payment methods must exist in the system
            """)
        else:
            st.warning("Template file not found. Please ensure the template file exists at the correct location.")
        
        # File uploader
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        if uploaded_file is not None:
            # Create a temporary file to save the uploaded content
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_path = tmp_file.name
            
            # Preview the uploaded data
            try:
                df = pd.read_csv(temp_path)
                st.subheader("Preview of data to be imported:")
                st.dataframe(df.head(5), use_container_width=True)
                
                # Check for required columns
                required_columns = ["amount", "category", "payment_method", "date", "description", "tag"]
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"CSV file is missing required columns: {', '.join(missing_columns)}")
                else:
                    # Import button
                    if st.button("Import Expenses"):
                        # Call the import function
                        result = csv_operations.import_expenses(temp_path)
                        
                        if result:
                            log_manager.add_log(log_manager.generate_log_description("import_expenses", [str(len(df))]))
                            st.success("Expenses imported successfully!")
                        else:
                            st.error("Failed to import expenses. Check the log for details.")
                
                # Clean up the temporary file
                os.unlink(temp_path)
                
            except Exception as e:
                st.error(f"Error reading CSV file: {e}")
                # Clean up the temporary file on error
                os.unlink(temp_path)
    
    # Export Tab
    with tab2:
        st.subheader("Export Expenses to CSV")
        
        # Set up export options
        sort_options = {
            "amount": "Amount",
            "category": "Category",
            "payment_method": "Payment Method",
            "date": "Date",
            "description": "Description",
            "tag": "Tag"
        }
        
        sort_field = st.selectbox("Sort by", list(sort_options.keys()), format_func=lambda x: sort_options[x])
        
        # Export button
        if st.button("Export Expenses"):
            # Create a temporary file for the export
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
                temp_path = tmp_file.name
            
            # Call the export function
            result = csv_operations.export_csv(temp_path, sort_field)
            
            if result:
                # Read the exported file for download
                with open(temp_path, "r") as f:
                    csv_data = f.read()
                
                # Generate a meaningful filename
                current_date = datetime.now().strftime("%Y%m%d")
                download_filename = f"expenses_{st.session_state.username}_{current_date}.csv"
                
                # Create download button
                st.download_button(
                    label="Download CSV File",
                    data=csv_data,
                    file_name=download_filename,
                    mime="text/csv"
                )
                
                log_manager.add_log(log_manager.generate_log_description("export_expenses"))
                st.success("Expenses exported successfully!")
                
                # Clean up the temporary file
                os.unlink(temp_path)
            else:
                st.error("Failed to export expenses. There might be no data to export.")