# Expensly - Expense Tracking System

<div align="center">
  <img src="expense_tracker/static/img/er_diagram_expense_reporting_app.png" alt="Expense Tracking System" width="500px"/>
  
  <p>A professional financial management application for tracking and analyzing expenses</p>
  
  [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://expensly.streamlit.app)
</div>

## Overview

Expensly is an enterprise-grade expense tracking system designed for both personal and organizational use. It provides comprehensive financial management through intuitive interfaces, powerful analytics, and secure data handling.

## Key Features

### Financial Management
- User authentication with role-based access control
- Complete expense lifecycle management (create, read, update, delete)
- Multi-dimensional categorization system with tags
- Configurable payment methods with masked sensitive data
- Streamlined account administration

### Analytics & Reporting
- Interactive data visualization dashboards
- Comprehensive expense analysis by multiple dimensions:
  - Category distribution and trends
  - Temporal analysis (monthly, quarterly, yearly)
  - Payment method utilization
  - Tag-based expenditure patterns
- Customizable reporting with powerful filtering capabilities

### Security & Administration
- Enterprise-level access control
- Detailed audit logging of system activities
- Data protection and privacy measures

## Web Interface

<div align="center">
  <img src="expense_tracker/static/img/detailed_relational_schema_expense_reporting_app.png" alt="Expensly Dashboard" width="650px"/>
</div>

The professional web application leverages Streamlit to provide:

- Responsive dashboard with KPI metrics
- Intuitive data entry forms with validation
- Cross-device compatibility
- Role-appropriate navigation and functions
- Real-time analytical processing

## Getting Started

### System Requirements

- Python 3.6 or higher
- Required Python packages (listed in requirements.txt):
  - streamlit
  - pandas
  - plotly
  - matplotlib
  - numpy

### Deployment Options

**Production Deployment**
- Access the live application at [https://expensly.streamlit.app](https://expensly.streamlit.app)

**Local Development**

1. Clone the repository
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Launch the application:
   ```powershell
   streamlit run streamlit_app.py
   ```

### Authentication

1. **New Users**: Register for an account via the registration interface
2. **Administrator Access**: Default credentials (for testing only)
   - Username: `admin`
   - Password: `admin`

## Data Management

### Import/Export Protocol

The system supports standardized CSV format:
```
amount,category,payment_method,date,description,tag,payment_detail_identifier
```

Example:
```
45.99,Groceries,Credit Card,2023-05-15,Weekly shopping,food,xxxx-xxxx-xxxx-1234
```

### Query Capabilities

The application implements a flexible filtering syntax:
```
<field> <operator> <value>
```

Parameters:
- Fields: amount, date, category, tag, payment_method, month
- Operators: =, <, >, <=, >=
- Multiple filters supported via comma separation

## User Roles & Permissions

### Administrator
- System configuration and maintenance
- User account management
- Reference data administration (categories, payment methods)
- Enterprise-wide analytics and audit reports

### Standard User
- Personal expense management
- Individual financial reporting
- Access to predefined categories and payment methods

## Application Architecture

### Interface Components

- **Dashboard**: Financial summary metrics and KPI visualization
- **Expense Management**: CRUD operations with filtering and search
- **Reports**: Parameterized reports with export capabilities
- **Administration**: Configuration and system monitoring (admin only)

### Technical Architecture

```
./
├── expense_tracker/           # Core package
│   ├── core/                  # Business logic layer
│   │   ├── category.py        # Category management
│   │   ├── expense.py         # Expense management
│   │   ├── payment.py         # Payment method management
│   │   ├── reporting.py       # Reporting functionality
│   │   └── user.py            # User management
│   ├── database/              # Data access layer
│   │   ├── connection.py      # Database connection handler
│   │   ├── db_init.py         # Database initialization
│   │   └── sql_queries.py     # SQL query definitions
│   ├── static/                # Static resources
│   │   ├── img/               # Images and diagrams
│   │   └── templates/         # CSV templates
│   ├── utils/                 # Utility modules
│   │   ├── csv_operations.py  # CSV import/export
│   │   └── logs.py            # Logging functionality
│   └── web/                   # Presentation layer
│       ├── app.py             # Main web application
│       └── pages/             # UI page components
├── .streamlit/                # Platform configuration
├── pyproject.toml             # Python project metadata
├── setup.py                   # Package installation script
├── streamlit_app.py           # Application entry point
├── requirements.txt           # Dependency specifications
└── README.md                  # Documentation
```

## Technical Details

### Troubleshooting

1. **Database Connectivity**: Ensure proper network configuration and database access permissions
2. **Data Import Issues**: Verify CSV format compliance with the specified schema
3. **Visualization Rendering**: For rendering issues, ensure browser compatibility and required JavaScript support
4. **Access Violations**: Confirm appropriate user role for the requested operation

### Security Considerations

- This application implements basic security measures suitable for development environments
- Sensitive payment information is intentionally masked in reports and exports
- For production deployment, additional security hardening is recommended

## Technology Stack

- **Frontend Framework**: Streamlit
- **Data Visualization**: Plotly, Matplotlib
- **Backend Language**: Python
- **Database**: SQLite (embedded)
- **Data Processing**: Pandas, NumPy
- **Deployment**: Streamlit Cloud

## License Information

This software is provided for educational and demonstration purposes. You may use and modify it for personal or educational use.

## Roadmap

Future development considerations include:
- Multi-currency support with exchange rate integration
- Advanced budget planning and forecasting
- Receipt digitization and OCR processing
- Cross-platform mobile application

## Usage Guide

1. Clone the repository and navigate to the project directory.

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Launch the application:
   ```powershell
   streamlit run streamlit_app.py
   ```

4. In the web interface, use the **Sign Up** tab to create a new user account (role 'user').

5. Login with your credentials via the **Login** tab.

6. As a regular user, you can:
   - Manage your own expenses (add, edit, delete)
   - View basic and advanced analytics dashboards
   - Import/export CSV data

7. To perform administrative tasks (manage users, categories, payment methods, and view logs), sign in as the default admin:
   - Username: `admin`
   - Password: `admin`

8. Once logged in as admin, use the sidebar navigation to access User Management, Category Management, Payment Method Management, and System Logs.
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

### Security Notes

- Database: SQLite is used for data storage (embedded database)
- Passwords are stored in plaintext for simplicity. In a production environment, implement proper password hashing.
- Payment method details are masked in reports and exports when they contain sensitive information.

## Contributing

To extend this project, consider adding:
- Multi-currency support
- Budget planning features
- Receipt image processing
- Cloud synchronization
