import sqlite3

def initialize_database(db_connection):
    """Initialize the database with all required tables."""
    
    cursor = db_connection.cursor()
    
    # Create User table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    
    # Create Role table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Role (
            role_id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Create User_Role table (many-to-many relationship)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User_Role (
            username TEXT,
            role_id INTEGER,
            PRIMARY KEY (username, role_id),
            FOREIGN KEY (username) REFERENCES User(username),
            FOREIGN KEY (role_id) REFERENCES Role(role_id)
        )
    ''')
    
    # Create Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Create Payment_Method table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Payment_Method (
            payment_method_id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_method_name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Create Tags table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Tags (
            tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Create Expense table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Expense (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT
        )
    ''')
    
    # Create Category_Expense table (many-to-many relationship)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Category_Expense (
            category_id INTEGER,
            expense_id INTEGER,
            PRIMARY KEY (category_id, expense_id),
            FOREIGN KEY (category_id) REFERENCES Categories(category_id),
            FOREIGN KEY (expense_id) REFERENCES Expense(expense_id)
        )
    ''')
    
    # Create Tag_Expense table (many-to-many relationship)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Tag_Expense (
            tag_id INTEGER,
            expense_id INTEGER,
            PRIMARY KEY (tag_id, expense_id),
            FOREIGN KEY (tag_id) REFERENCES Tags(tag_id),
            FOREIGN KEY (expense_id) REFERENCES Expense(expense_id)
        )
    ''')
    
    # Create Payment_Method_Expense table (many-to-many relationship with additional data)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Payment_Method_Expense (
            payment_method_id INTEGER,
            expense_id INTEGER,
            payment_detail_identifier TEXT,
            PRIMARY KEY (payment_method_id, expense_id),
            FOREIGN KEY (payment_method_id) REFERENCES Payment_Method(payment_method_id),
            FOREIGN KEY (expense_id) REFERENCES Expense(expense_id)
        )
    ''')
    
    # Create User_Expense table (many-to-many relationship)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User_Expense (
            username TEXT,
            expense_id INTEGER,
            PRIMARY KEY (username, expense_id),
            FOREIGN KEY (username) REFERENCES User(username),
            FOREIGN KEY (expense_id) REFERENCES Expense(expense_id)
        )
    ''')
    
    # Create Logs table (renamed from Activity_Log)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            activity_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            details TEXT,
            description TEXT,
            FOREIGN KEY (username) REFERENCES User(username)
        )
    ''')
    
    # Insert default roles
    cursor.execute("INSERT OR IGNORE INTO Role (role_name) VALUES ('admin')")
    cursor.execute("INSERT OR IGNORE INTO Role (role_name) VALUES ('user')")
    
    # Insert default admin user
    cursor.execute("INSERT OR IGNORE INTO User (username, password) VALUES ('admin', 'admin')")
    
    # Get admin role ID
    cursor.execute("SELECT role_id FROM Role WHERE role_name = 'admin'")
    admin_role_id = cursor.fetchone()[0]
    
    # Assign admin role to admin user
    cursor.execute("INSERT OR IGNORE INTO User_Role (username, role_id) VALUES ('admin', ?)", (admin_role_id,))
    
    # Insert default categories
    default_categories = ['Food', 'Transportation', 'Housing', 'Entertainment', 'Health', 'Shopping', 'Utilities', 'Miscellaneous']
    for category in default_categories:
        cursor.execute("INSERT OR IGNORE INTO Categories (category_name) VALUES (?)", (category.lower(),))
    
    # Insert default payment methods
    default_payment_methods = ['Cash', 'Credit Card', 'Debit Card', 'UPI', 'Net Banking', 'Check', 'Digital Wallet']
    for method in default_payment_methods:
        cursor.execute("INSERT OR IGNORE INTO Payment_Method (payment_method_name) VALUES (?)", (method.lower(),))
    
    # Commit the changes
    db_connection.commit()