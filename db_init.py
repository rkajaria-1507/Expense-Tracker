"""
Database initialization script for the Expense Tracking System.
Creates all necessary tables if they don't exist.
"""

import sqlite3
import os

def initialize_database(conn=None, db_name="ExpenseReport"):
    """Initialize the database with all required tables"""
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(db_name)
        close_conn = True
        
    cursor = conn.cursor()
    
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
            role_id INTEGER PRIMARY KEY,
            role_name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Create user_role table (many-to-many relationship)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_role (
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
            category_id INTEGER PRIMARY KEY,
            category_name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Create Tags table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Tags (
            tag_id INTEGER PRIMARY KEY,
            tag_name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Create Payment_Method table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Payment_Method (
            payment_method_id INTEGER PRIMARY KEY,
            payment_method_name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Create Expense table (main entity)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Expense (
            expense_id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT
        )
    ''')
    
    # Create category_expense table (many-to-many relationship)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS category_expense (
            category_id INTEGER,
            expense_id INTEGER,
            PRIMARY KEY (category_id, expense_id),
            FOREIGN KEY (category_id) REFERENCES Categories(category_id),
            FOREIGN KEY (expense_id) REFERENCES Expense(expense_id)
        )
    ''')
    
    # Create tag_expense table (many-to-many relationship)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tag_expense (
            tag_id INTEGER,
            expense_id INTEGER,
            PRIMARY KEY (tag_id, expense_id),
            FOREIGN KEY (tag_id) REFERENCES Tags(tag_id),
            FOREIGN KEY (expense_id) REFERENCES Expense(expense_id)
        )
    ''')
    
    # Create payment_method_expense table (many-to-many relationship with additional attributes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_method_expense (
            payment_method_id INTEGER,
            expense_id INTEGER,
            payment_detail_identifier TEXT,
            PRIMARY KEY (payment_method_id, expense_id),
            FOREIGN KEY (payment_method_id) REFERENCES Payment_Method(payment_method_id),
            FOREIGN KEY (expense_id) REFERENCES Expense(expense_id)
        )
    ''')
    
    # Create user_expense table (many-to-many relationship)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_expense (
            username TEXT,
            expense_id INTEGER,
            PRIMARY KEY (username, expense_id),
            FOREIGN KEY (username) REFERENCES User(username),
            FOREIGN KEY (expense_id) REFERENCES Expense(expense_id)
        )
    ''')
    
    # Create Logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Logs (
            logid INTEGER PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            username TEXT,
            description TEXT,
            FOREIGN KEY (username) REFERENCES User(username)
        )
    ''')
    
    # Insert default roles if they don't exist
    cursor.execute("INSERT OR IGNORE INTO Role (role_id, role_name) VALUES (1, 'admin')")
    cursor.execute("INSERT OR IGNORE INTO Role (role_id, role_name) VALUES (2, 'user')")
    
    # Create admin user if it doesn't exist
    cursor.execute("SELECT COUNT(*) FROM User WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO User (username, password) VALUES ('admin', 'admin')")
        cursor.execute("INSERT INTO user_role (username, role_id) VALUES ('admin', 1)")
    
    conn.commit()
    
    if close_conn:
        conn.close()
        print("Database initialized successfully!")
    
    return conn, cursor

def reset_database(db_name="ExpenseReport"):
    """Delete the database file and reinitialize it"""
    if os.path.exists(db_name):
        os.remove(db_name)
        print(f"Existing database '{db_name}' has been deleted.")
    
    return initialize_database(None, db_name)

if __name__ == "__main__":
    # When run directly, initialize the database
    initialize_database()
