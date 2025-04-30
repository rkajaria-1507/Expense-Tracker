# Expense Tracking System

# A comprehensive application for tracking and analyzing personal or organizational expenses, providing a modern Streamlit web interface.

## Overview

This system allows users to add, manage, and analyze expenses with multiple categories, payment methods, and tags. It features robust reporting capabilities, CSV import/export functionality, and a role-based access control system.

## Features

- **User Management**: Registration, authentication, and role-based permissions
- **Expense Tracking**: Add, update, delete, and list expenses
- **Categorization**: Organize expenses by categories and tags
- **Payment Methods**: Track expenses by different payment methods
- **Account Deletion**: Users and admins can permanently delete accounts along with all associated data via confirmation prompts
- **Data Import/Export**: CSV file support for bulk operations
- **Advanced Reporting**: Multiple report types including:
  - Top N expenses
  - Category spending analysis
  - Monthly category breakdowns
  - Above-average expenses
  - Payment method usage
  - Tag-based analysis
  - Data visualization

## New Features

- **Logs Module:**  
  The system now maintains detailed logs of user actions (e.g., login/logout, adding users, expense operations, report generation).  
  Administrators can view logs via the `view_logs` command.

- **Enhanced Reporting:**  
  New reporting functions have been implemented including:
  - `report payment_method_details_expense` - Analyzes payment method details with masking of sensitive information.
  - `report analyze_expenses` - Generates a comprehensive dashboard for expense analytics with customizable filters.

- **Web Interface:**  
  A modern web application built with Streamlit that provides:
  - Interactive dashboards with data visualizations
  - User-friendly forms for data entry and management
  - Responsive design for desktop and mobile access
  - Role-based navigation and permissions
  - Real-time analytics and reporting

## Installation

### Prerequisites

- Python 3.6+
- SQLite3 (included in Python standard library)
- Required Python packages:
  - matplotlib
  - numpy
  - streamlit
  - pandas
  - plotly

### Libraries Used

This project uses the following libraries:
- **External libraries** (need installation):
  - matplotlib - Data visualization for CLI
  - numpy - Numerical calculations
  - streamlit - Web interface
  - pandas - Data manipulation
  - plotly - Interactive web visualizations

- **Standard library** (included with Python):
  - sqlite3 - Database operations
  - csv - CSV file handling
  - datetime - Date and time operations
  - shlex - Command parsing (CLI)
  - subprocess - Process management
  - os, sys - System operations

### Setup

1. Clone or download this repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the application using the launcher script:
   ```
   run_expense_tracker.bat
   ```
   It will install dependencies if needed and launch the Streamlit web interface.

## Web Interface

The web interface provides a more user-friendly way to interact with the expense tracking system. It includes:

### Dashboard
- Summary metrics of expenses
- Interactive charts for expense analysis by category, month, payment method, and tag
- Recent expense listing

### User Management (Admin)
- Add, view, and manage users
- Set user roles and permissions

### Category & Payment Management (Admin)
- Add and manage expense categories
- Add and manage payment methods

### Expense Management
- Add, edit, and delete expenses
- Filter and search expenses
- Bulk operations

### Reports
- Basic reports with interactive filters
- Advanced analytics with comprehensive dashboards
- Data export options

### Import/Export
- CSV file import with validation
- Export filtered data to CSV

### System Logs (Admin)
- View detailed system and user activity logs
- Filter logs by user, action, or date

## Filtering Data

Many commands and features support filtering with the following syntax:
```
<field> <operator> <value>
```

Where:
- `field` can be: amount, date, category, tag, payment_method, month
- `operator` can be: =, <, >, <=, >=
- Multiple filters can be combined with commas

Example:
```
listexpenses amount > 100, category = food, month = january
```

## User Roles

### Admin
- Has access to all functions except expense functions such as add, delete, modify
- Can manage users, categories, and payment methods
- Has access to system-wide reports and logs

### User
- Can manage own expenses
- Can view own reports
- Limited to viewing/using existing categories and payment methods

## Import/Export Format

The expected CSV format for import/export is:
```
amount,category,payment_method,date,description,tag,payment_detail_identifier
```

Example template is available in `import_expenses_template.csv`

## Project Structure

The project has been reorganized into a proper Python package structure:

```
expense-tracker/
├── expense_tracker/           # Main package
│   ├── __init__.py
│   ├── config/                # Configuration
│   │   ├── __init__.py
│   │   └── constants.py
│   ├── core/                  # Core functionality
│   │   ├── __init__.py
│   │   ├── category.py
│   │   ├── expense.py
│   │   ├── payment.py
│   │   ├── reporting.py
│   │   └── user.py
│   ├── database/              # Database operations
│   │   ├── __init__.py
│   │   ├── db_init.py
│   │   ├── sql_queries.py
│   │   └── ExpenseReport      # SQLite database file
│   ├── utils/                 # Utility functions
│   │   ├── __init__.py
│   │   ├── csv_operations.py
│   │   ├── logs.py
│   │   └── parser.py
│   ├── web/                   # Web interface
│   │   ├── __init__.py
│   │   ├── app.py
│   │   └── pages/             # Web interface page components
│   │       ├── __init__.py
│   │       ├── advanced_reports.py
│   │       ├── basic_reports.py
│   │       ├── category_management.py
│   │       ├── import_export.py
│   │       ├── manage_expenses.py
│   │       ├── payment_management.py
│   │       ├── system_logs.py
│   │       └── user_management.py
│   └── tests/                 # Test cases
│       └── __init__.py
├── main.py                    # CLI entry point
├── run_expense_tracker.bat    # Launcher script
├── requirements.txt           # Dependencies
├── setup.py                   # Package installer
├── README.md                  # Documentation
└── import_expenses_template.csv  # CSV template
```

## Getting Started

1. Launch the application by running the launcher script:
   ```
   run_expense_tracker.bat
   ```
   This will install dependencies if needed and open the Streamlit web interface.

2. In the web interface, use the **Sign Up** tab to create a new user account (role 'user').

3. Login with your credentials via the **Login** tab.

4. As a regular user, you can:
   - Manage your own expenses (add, edit, delete)
   - View basic and advanced analytics dashboards
   - Import/export CSV data

5. To perform administrative tasks (manage users, categories, payment methods, and view logs), sign in as the default admin:
   - Username: `admin`
   - Password: `admin`

6. Once logged in as admin, use the sidebar navigation to access User Management, Category Management, Payment Method Management, and System Logs.
   After setup, you can log out and use the system as a regular user for expense tracking and reporting.

## Troubleshooting

### Common Issues

1. **Database Errors**: If you encounter database errors, check if the SQLite database file has proper permissions.

2. **Import Failures**: Ensure your CSV file matches the expected format exactly. Check for extra spaces, missing fields, or incorrect date formats.

3. **Visualization Issues**: If charts don't display:
   - Verify matplotlib and numpy are installed
   - Try running in a different terminal that supports graphical output
   - For remote connections, ensure X11 forwarding is enabled

4. **Permission Errors**: Make sure you're logged in with the appropriate role for the command you're trying to run.

### Error Messages

- "Error: Username does not exist" - Check spelling or register a new user
- "Error: Category does not exist" - Add the category or use an existing one
- "Error: Unauthorized command" - Log in with a user that has appropriate permissions

## Security Notes

- Passwords are stored in plaintext for simplicity. In a production environment, implement proper password hashing.
- Payment method details are masked in reports and exports when they contain sensitive information.

## License

This project is provided as an educational tool. Feel free to use and modify for personal or educational purposes.

## Contributing

To extend this project, consider adding:
- Multi-currency support
- Budget planning features
- Receipt image processing
- Cloud synchronization
