@echo off
 echo ===================================
 echo Expense Tracker Application Launcher
 echo ===================================
 echo.
 echo 1. Launch Streamlit Web Interface
 echo 2. Exit
 echo.
 set /p option="Select an option (1-2): "

 if "%option%"=="1" (
     echo.
     echo Launching Web Interface...
     
     REM Check for required packages
     pip show streamlit >nul 2>&1
     if errorlevel 1 (
         echo Installing required packages...
         pip install -r requirements.txt
     )
     
     REM Create the database directory if it doesn't exist
     if not exist "expense_tracker\database" mkdir "expense_tracker\database"
     if not exist "expense_tracker\database\ExpenseReport" (
         echo No database file found. A new one will be created at expense_tracker\database\ExpenseReport
     ) else (
         echo Using existing database at expense_tracker\database\ExpenseReport
     )
     
     echo Starting Streamlit server...
     streamlit run expense_tracker/web/app.py
     if errorlevel 1 (
         echo Failed to start Streamlit server.
         echo Please ensure you have Streamlit installed: pip install streamlit
         pause
     )
 ) else if "%option%"=="2" (
     echo.
     echo Exiting...
     exit /b
 ) else (
     echo.
     echo Invalid option. Please try again.
     pause
 )

 exit /b