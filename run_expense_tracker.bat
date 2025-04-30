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
     
     REM Database file synchronization logic
     if exist "ExpenseReport" (
         if not exist "expense_tracker\database\ExpenseReport" (
             echo Copying database file to package location...
             copy "ExpenseReport" "expense_tracker\database\ExpenseReport" > nul
         ) else (
             echo Both database files exist. Using the package version.
             echo To use the root version instead, delete the package version first.
         )
     ) else (
         if exist "expense_tracker\database\ExpenseReport" (
             echo Using existing package database.
         ) else (
             echo No database file found. A new one will be created.
         )
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