import streamlit as st
import os
import sys

# Print debugging information
st.write("## Environment Information")
st.write(f"Python version: {sys.version}")
st.write(f"Current working directory: {os.getcwd()}")
st.write(f"Files in current directory: {os.listdir('.')}")

# Try importing from the expense_tracker package
try:
    from expense_tracker.web.app import main
    st.success("Successfully imported expense_tracker package")
    
    # Display app with main function
    st.write("## Expense Tracker App")
    main()
except Exception as e:
    st.error(f"Error importing expense_tracker package: {e}")
    st.error(f"Python path: {sys.path}")
    
    # Try to list files in the expense_tracker directory
    try:
        tracker_path = os.path.join(os.getcwd(), 'expense_tracker')
        if os.path.exists(tracker_path):
            st.write(f"Files in expense_tracker directory: {os.listdir(tracker_path)}")
        else:
            st.error(f"expense_tracker directory not found at: {tracker_path}")
    except Exception as inner_e:
        st.error(f"Error listing files: {inner_e}")
