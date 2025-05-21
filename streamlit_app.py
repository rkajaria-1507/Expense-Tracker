# streamlit_app.py - Entry point for Streamlit Cloud
import streamlit as st
import os
import sys

# Add the current directory to the path to help Python find the expense_tracker package
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the main app function
try:
    from expense_tracker.web.app import main
    
    # Show a small debug section in the sidebar that can be expanded
    with st.sidebar.expander("Debug Info (Click to expand)", expanded=False):
        st.write(f"Python version: {sys.version}")
        st.write(f"Current directory: {os.getcwd()}")
        st.write(f"Files in current directory: {os.listdir('.')}")
        st.write(f"Python path: {sys.path}")
    
    # Run the main application
    main()
    
except Exception as e:
    import traceback
    
    st.error(f"Error importing or running the app: {str(e)}")
    st.error("Please check the logs for more details.")
    
    # Display the full traceback for debugging
    st.code(traceback.format_exc(), language="python")
    
    # Try to provide helpful debug information
    st.write("### Debug Information")
    st.write(f"Python path: {sys.path}")
    
    # Check if expense_tracker directory exists
    if os.path.exists(os.path.join(current_dir, 'expense_tracker')):
        st.write(f"expense_tracker directory exists at {os.path.join(current_dir, 'expense_tracker')}")
        st.write(f"Contents: {os.listdir(os.path.join(current_dir, 'expense_tracker'))}")
    else:
        st.error(f"expense_tracker directory NOT found at {os.path.join(current_dir, 'expense_tracker')}")