@echo off
echo Installing required packages...
pip install streamlit pandas plotly
echo.
echo Starting Expense Tracker application...
python -m streamlit run streamlit_app.py
pause