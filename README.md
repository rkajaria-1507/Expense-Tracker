# Expense Tracking System

A command-line database application for tracking and analyzing personal or organizational expenses.

## Overview

This system allows users to add, manage, and analyze expenses with multiple categories, payment methods, and tags. It features robust reporting capabilities, CSV import/export functionality, and a role-based access control system.

## Features

- **User Management**: Registration, authentication, and role-based permissions
- **Expense Tracking**: Add, update, delete, and list expenses
- **Categorization**: Organize expenses by categories and tags
- **Payment Methods**: Track expenses by different payment methods
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

- **Test Cases:**  
  Comprehensive test cases have been added to validate new features such as logs, enhanced reporting, and CSV operations.  
  These tests can be run to ensure the integrity of the application.

## Installation

### Prerequisites

- Python 3.6+
- SQLite3 (included in Python standard library)
- Required Python packages:
  - matplotlib
  - numpy

### Libraries Used

This project uses the following libraries:
- **External libraries** (need installation):
  - matplotlib - Data visualization
  - numpy - Numerical calculations

- **Standard library** (included with Python):
  - sqlite3 - Database operations
  - csv - CSV file handling
  - datetime - Date and time operations
  - shlex - Command parsing
  - subprocess - Process management
  - os, sys - System operations

### Setup

1. Clone or download this repository
2. Install required packages using one of these methods:
   ```
   # Option 1: Install manually
   pip install -r requirements.txt
   
   # Option 2: Let the app install requirements automatically
   # (The app will check and install requirements on first run)
   ```
3. Run the main application:
   ```
   python main.py
   ```

## Database Structure

The application uses SQLite with the following tables:
- User
- Role
- user_role
- Categories
- Tags
- Payment_Method
- Expense
- category_expense
- tag_expense
- payment_method_expense
- user_expense

## Commands

### Authentication

- `login <username> <password>` - Log in to the system
- `logout` - Log out of the system

### User Management (Admin Only)

- `add_user <username> <password> <role>` - Create a new user
- `list_users` - List all registered users

### Category Management

- `list_categories` - List all expense categories
- `add_category <category_name>` - Add a new category (Admin only)

### Payment Methods

- `list_payment_methods` - List all payment methods
- `add_payment_method <payment_method_name>` - Add a new payment method (Admin only)

### Expense Management

- `add_expense <amount> <category> <payment_method> <date> <description> <tag>` - Add a new expense
- `update_expense <expense_id> <field> <new_value>` - Update an existing expense
- `delete_expense <expense_id>` - Delete an expense
- `list_expenses [<field> <operator> <value>, ...]` - List expenses with optional filters

### CSV Operations

- `import_expenses <file_path>` - Import expenses from a CSV file
- `export_csv <file_path> [, sort-on <field_name>]` - Export expenses to a CSV file

### Reporting

- `report top_expenses <N> <start_date> <end_date>` - Show top N expenses in a date range
- `report category_spending <category>` - Analyze spending for a specific category
- `report above_average_expenses` - Show expenses above their category average
- `report monthly_category_spending` - Show monthly spending by category
- `report payment_method_usage` - Show spending breakdown by payment method
- `report frequent_category` - Show most frequently used categories
- `report tag_expenses` - Show expenses by tag
- `report payment_method_details_expense` - Analyze payment method details (User only)
- `report highest_spender_per_month` - Show highest spender each month (Admin only)
- `report analyze_expenses [<field> <operator> <value>, ...]` - Dashboard with filtered analytics

### Logs

- `view_logs` - View detailed logs of user actions (Admin only)

### General

- `help` - Show available commands for current user role

## Filtering Data

Many commands support filtering with the following syntax:
```
<field> <operator> <value>
```

Where:
- `field` can be: amount, date, category, tag, payment_method, month
- `operator` can be: =, <, >, <=, >=
- Multiple filters can be combined with commas

Example:
```
list_expenses amount > 100, category = food, month = january
```

## User Roles

### Admin
- Has access to all features
- Can manage users, categories, and payment methods
- Has access to system-wide reports

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

## Visualizations

The reporting system generates visualizations for data analysis including:
- Bar charts
- Pie charts
- Line graphs
- Histograms
- Time series charts

## Development Structure

- `main.py`: Entry point and main application loop
- `user.py`: User authentication and management
- `category.py`: Category management
- `payment.py`: Payment method management
- `expense.py`: Core expense tracking functionality
- `reporting.py`: Analysis and visualization features
- `csv_operations.py`: Data import/export utilities
- `parser.py`: Command parsing and routing
- `constants.py`: System-wide constants and privileges
- `log_manager.py`: Logs module to record user actions *(new)*

## Project Structure

```
DBMS_assignment/
├── main.py               # Application entry point
├── user.py               # User management and authentication
├── category.py           # Category operations
├── payment.py            # Payment method operations  
├── expense.py            # Core expense functionality
├── csv_operations.py     # CSV import/export utilities
├── reporting.py          # Data analysis and visualization features (new reporting functions included)
├── parser.py             # Command parsing and routing
├── constants.py          # System permissions and constants
├── log_manager.py        # Logs module to record user actions *(new)*
├── ExpenseReport         # SQLite database file
└── import_expenses_template.csv  # CSV template
```

## Example Usage

### Basic Workflow

```
login admin password123
add_category groceries
add_payment_method credit_card
add_expense 45.99 groceries credit_card 2023-06-15 "Weekly shopping" food
list_expenses
report category_spending groceries
export_csv my_expenses.csv
logout
```

### Advanced Filtering

```
login user1 pass123
list_expenses amount > 50, category = entertainment, date >= 2023-01-01
report analyze_expenses category = food, month = january
```

## Data Visualization Examples

The reporting system generates interactive visualizations for better data comprehension:

- Category spending reports show pie charts of proportional spending
- Monthly trends appear as line or bar charts
- Payment method analysis includes comparative visualizations
- Expense analytics dashboards combine multiple chart types

## Logs and Test Cases

### Logs

The system maintains detailed logs of user actions such as login/logout, adding users, expense operations, and report generation.  
Administrators can view these logs using the `view_logs` command.

### Test Cases

Comprehensive test cases have been added to validate the following features:
- Logs functionality
- Enhanced reporting functions
- CSV import/export operations

These tests ensure the integrity and reliability of the application.

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

## Getting Started

For new users:

1. Start the application: `python main.py`

2. Login with default admin account:
   ```
   login admin admin123
   ```

3. Create your own user:
   ```
   add_user myusername mypassword user
   ```

4. Add categories and payment methods:
   ```
   add_category food
   add_category utilities
   add_payment_method cash
   add_payment_method credit
   ```

5. Logout and login as new user:
   ```
   logout
   login myusername mypassword
   ```

6. Add expenses and generate reports!

## Security Notes

- Passwords are stored in plaintext for simplicity. In a production environment, implement proper password hashing.
- Payment method details are masked in reports and exports when they contain sensitive information.

## License

This project is provided as an educational tool. Feel free to use and modify for personal or educational purposes.

## Contributing

To extend this project, consider adding:
- Web interface
- Multi-currency support
- Budget planning features
- Receipt image processing
- Cloud synchronization
