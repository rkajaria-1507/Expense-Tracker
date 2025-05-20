import streamlit as st
import sys
import os

# Add the project root to the path to ensure imports work
# This ensures the expense_tracker package is in the path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Display the current directory and Python path for debugging
st.sidebar.write("### Debug Information")
st.sidebar.write(f"Current directory: {os.getcwd()}")
st.sidebar.write(f"Directory contents: {os.listdir('.')}")
st.sidebar.write(f"Python path: {sys.path[:3]}...")

# Import and run the main app
try:
    from expense_tracker.web.app import main
    main()
except ImportError as e:
    st.error(f"Failed to import main app module: {e}")
    
    # Show more detailed import error information
    import traceback
    st.code(traceback.format_exc())
    
    # Try to list directories to help debug
    st.write("### Project Structure:")
    if os.path.exists("expense_tracker"):
        st.write(f"expense_tracker directory contents: {os.listdir('expense_tracker')}")
        if os.path.exists("expense_tracker/web"):
            st.write(f"expense_tracker/web contents: {os.listdir('expense_tracker/web')}")