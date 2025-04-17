import sqlite3
import sys
from user import UserManager
from category import CategoryManager
from payment import PaymentManager
from expense import ExpenseManager
from csv_operations import CSVOperations
from reporting import ReportManager
from parser import CommandParser
from logs import LogManager
import subprocess
import os
from db_init import initialize_database  # Add this import

def display_welcome_screen():
    print(r"""
           Welcome to the Expense Reporting App!
        📊 Track • 💸 Manage • 📁 Import/Export • 📈 Analyze

             Powered by: Pratik, Don Raghav, Deevan
               ----------------------------------

💼 Features:
* Multi-User Login with Role-Based Access (Admin/User)
* Add / Edit / Delete / View Expenses
* Categorize Spending by Type and Payment Method
* Import and Export Expenses via CSV
* Insightful Reports: Top Expenses, Monthly Spendings, etc.
* Log Files for System & User Activity Tracking
* Advanced Analytics for Spending Patterns
* Visualization of Reports and Trends
* Dashboards for Monthly & Category-wise Insights

✨ Type 'help' to get started with available commands!
""")

def check_and_install_requirements():
    """Check if required packages are installed and install them if necessary."""
    try:
        # Try to import required packages
        import matplotlib
        import numpy
        print("All required packages are already installed.")
    except ImportError:
        print("Some required packages are missing. Installing now...")
        
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        requirements_file = os.path.join(current_dir, "requirements.txt")
        
        if os.path.exists(requirements_file):
            try:
                # Install requirements using pip
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
                print("Required packages installed successfully.")
            except subprocess.CalledProcessError:
                print("Failed to install required packages. Please install them manually:")
                print("pip install -r requirements.txt")
                sys.exit(1)
        else:
            print("Requirements file not found. Please install matplotlib and numpy manually.")
            sys.exit(1)
            
            
def main():
    # Check and install requirements first
    check_and_install_requirements()
    
    # Connect to the database
    conn = sqlite3.connect("ExpenseReport")  # Creates/opens a database file
    cursor = conn.cursor()  # Creates a cursor object to execute SQL commands
    
    # Initialize database tables if they don't exist
    initialize_database(conn)  # Add this line
    
    # Initialize managers
    user_manager = UserManager(cursor, conn)
    category_manager = CategoryManager(cursor, conn)
    payment_manager = PaymentManager(cursor, conn)
    expense_manager = ExpenseManager(cursor, conn)
    
    # Initialize managers that depend on other managers
    csv_operations = CSVOperations(cursor, conn, expense_manager)
    report_manager = ReportManager(cursor, conn)
    log_manager = LogManager(cursor, conn)
    
    # Create command parser
    command_parser = CommandParser(
        user_manager, 
        category_manager, 
        payment_manager, 
        expense_manager, 
        csv_operations, 
        report_manager, 
        log_manager
    )
    
    # Display the welcome screen
    display_welcome_screen()
    
    # Main loop
    while True:
        try:
            # Show prompt with different style based on login status
            if command_parser.user_manager.current_user:
                username = command_parser.user_manager.current_user
                role = command_parser.user_manager.privileges
                prompt = f"[{username}@{role}]> "
            else:
                prompt = "guest> "
                
            cmd_string = input(prompt)
            
            if cmd_string.strip().lower() == "exit":
                print("\n" + "─" * 60)
                print("Exiting application. Goodbye!".center(60))
                print("─" * 60 + "\n")
                break
                
            # Add spacing before command execution
            print()
            command_parser.parse(cmd_string)
            # Add spacing after command execution
            print()
            
        except KeyboardInterrupt:
            print("\n\n" + "─" * 60)
            print("Exiting due to keyboard interrupt...".center(60))
            print("─" * 60 + "\n")
            break
            
        except Exception as e:
            print("\n" + "─" * 60)
            print("❌ An unexpected error occurred:".center(60))
            print(str(e).center(60))
            print("─" * 60 + "\n")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    main()



