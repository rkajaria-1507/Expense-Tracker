import sqlite3
import os
import unittest
from unittest.mock import patch
import io
import sys
import csv
import tempfile
import shutil

# Import all modules
from user import UserManager
from category import CategoryManager
from payment import PaymentManager
from expense import ExpenseManager
from csv_operations import CSVOperations
from reporting import ReportManager

class TestExpenseSystem(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Create a test database in memory - this doesn't affect the real application database
        # Tests run against this isolated in-memory database to prevent modifying actual data
        cls.conn = sqlite3.connect(':memory:')
        cls.cursor = cls.conn.cursor()
        
        # Create necessary tables for testing purposes only
        cls.create_test_db_schema()
        
        # Initialize managers
        cls.user_manager = UserManager(cls.cursor, cls.conn)
        cls.category_manager = CategoryManager(cls.cursor, cls.conn)
        cls.payment_manager = PaymentManager(cls.cursor, cls.conn)
        cls.expense_manager = ExpenseManager(cls.cursor, cls.conn)
        cls.csv_operations = CSVOperations(cls.cursor, cls.conn, cls.expense_manager)
        cls.report_manager = ReportManager(cls.cursor, cls.conn)
        
        # Set up initial test data
        cls.setup_test_data()
        
        # Create a temp directory for file operations
        cls.temp_dir = tempfile.mkdtemp()
    
    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        # Remove temp directory
        shutil.rmtree(cls.temp_dir)
    
    @classmethod
    def create_test_db_schema(cls):
        # Create the database schema matching the actual application
        cls.cursor.execute('''
            CREATE TABLE User (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')
        
        cls.cursor.execute('''
            CREATE TABLE Role (
                role_id INTEGER PRIMARY KEY,
                role_name TEXT UNIQUE NOT NULL
            )
        ''')
        
        cls.cursor.execute('''
            CREATE TABLE user_role (
                username TEXT,
                role_id INTEGER,
                PRIMARY KEY (username, role_id),
                FOREIGN KEY (username) REFERENCES User(username),
                FOREIGN KEY (role_id) REFERENCES Role(role_id)
            )
        ''')
        
        cls.cursor.execute('''
            CREATE TABLE Categories (
                category_id INTEGER PRIMARY KEY,
                category_name TEXT UNIQUE NOT NULL
            )
        ''')
        
        cls.cursor.execute('''
            CREATE TABLE Tags (
                tag_id INTEGER PRIMARY KEY,
                tag_name TEXT UNIQUE NOT NULL
            )
        ''')
        
        cls.cursor.execute('''
            CREATE TABLE Payment_Method (
                payment_method_id INTEGER PRIMARY KEY,
                payment_method_name TEXT UNIQUE NOT NULL
            )
        ''')
        
        cls.cursor.execute('''
            CREATE TABLE Expense (
                expense_id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT
            )
        ''')
        
        cls.cursor.execute('''
            CREATE TABLE category_expense (
                category_id INTEGER,
                expense_id INTEGER,
                PRIMARY KEY (category_id, expense_id),
                FOREIGN KEY (category_id) REFERENCES Categories(category_id),
                FOREIGN KEY (expense_id) REFERENCES Expense(expense_id)
            )
        ''')
        
        cls.cursor.execute('''
            CREATE TABLE tag_expense (
                tag_id INTEGER,
                expense_id INTEGER,
                PRIMARY KEY (tag_id, expense_id),
                FOREIGN KEY (tag_id) REFERENCES Tags(tag_id),
                FOREIGN KEY (expense_id) REFERENCES Expense(expense_id)
            )
        ''')
        
        cls.cursor.execute('''
            CREATE TABLE payment_method_expense (
                payment_method_id INTEGER,
                expense_id INTEGER,
                payment_detail_identifier TEXT,
                PRIMARY KEY (payment_method_id, expense_id),
                FOREIGN KEY (payment_method_id) REFERENCES Payment_Method(payment_method_id),
                FOREIGN KEY (expense_id) REFERENCES Expense(expense_id)
            )
        ''')
        
        cls.cursor.execute('''
            CREATE TABLE user_expense (
                username TEXT,
                expense_id INTEGER,
                PRIMARY KEY (username, expense_id),
                FOREIGN KEY (username) REFERENCES User(username),
                FOREIGN KEY (expense_id) REFERENCES Expense(expense_id)
            )
        ''')
        
        cls.conn.commit()
    
    @classmethod
    def setup_test_data(cls):
        # Insert basic test data
        
        # Roles
        cls.cursor.execute("INSERT INTO Role (role_id, role_name) VALUES (1, 'admin')")
        cls.cursor.execute("INSERT INTO Role (role_id, role_name) VALUES (2, 'user')")
        
        # Admin user
        cls.cursor.execute("INSERT INTO User (username, password) VALUES ('admin', 'admin123')")
        cls.cursor.execute("INSERT INTO user_role (username, role_id) VALUES ('admin', 1)")
        
        # Regular user
        cls.cursor.execute("INSERT INTO User (username, password) VALUES ('testuser', 'password123')")
        cls.cursor.execute("INSERT INTO user_role (username, role_id) VALUES ('testuser', 2)")
        
        # Categories
        cls.cursor.execute("INSERT INTO Categories (category_name) VALUES ('food')")
        cls.cursor.execute("INSERT INTO Categories (category_name) VALUES ('rent')")
        
        # Payment methods
        cls.cursor.execute("INSERT INTO Payment_Method (payment_method_name) VALUES ('cash')")
        cls.cursor.execute("INSERT INTO Payment_Method (payment_method_name) VALUES ('credit_card')")
        
        cls.conn.commit()
    
    # Helper method to capture stdout
    def capture_output(self, func, *args, **kwargs):
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput
        result = func(*args, **kwargs)
        sys.stdout = sys.__stdout__
        return capturedOutput.getvalue(), result
    
    # ============= USER MANAGER TESTS =============
    
    def test_user_authentication_success(self):
        # Test successful login
        output, result = self.capture_output(self.user_manager.authenticate, 'admin', 'admin123')
        self.assertTrue(result)
        self.assertEqual(self.user_manager.current_user, 'admin')
        self.assertEqual(self.user_manager.privileges, 'admin')
        self.assertIn("Welcome, admin! You are logged in as admin.", output)
    
    def test_user_authentication_wrong_password(self):
        # Test login with wrong password
        self.user_manager.logout()  # Logout first
        output, result = self.capture_output(self.user_manager.authenticate, 'admin', 'wrongpassword')
        self.assertFalse(result)
        self.assertIsNone(self.user_manager.current_user)
        self.assertIn("Incorrect password", output)
    
    def test_user_authentication_nonexistent_user(self):
        # Test login with non-existent username
        output, result = self.capture_output(self.user_manager.authenticate, 'nonexistent', 'password')
        self.assertFalse(result)
        self.assertIn("Username does not exist", output)
    
    def test_user_logout(self):
        # Test user logout
        self.user_manager.authenticate('admin', 'admin123')  # Login first
        output, result = self.capture_output(self.user_manager.logout)
        self.assertTrue(result)
        self.assertIsNone(self.user_manager.current_user)
        self.assertIsNone(self.user_manager.privileges)
        self.assertIn("Logging Out", output)
    
    def test_user_register_success(self):
        # Test successful user registration
        self.user_manager.authenticate('admin', 'admin123')  # Login as admin
        output, result = self.capture_output(self.user_manager.register, 'newuser', 'password123', 'user')
        self.assertTrue(result)
        self.assertIn("User added successfully", output)
        
        # Verify user was added
        self.cursor.execute("SELECT username FROM User WHERE username = ?", ('newuser',))
        user = self.cursor.fetchone()
        self.assertIsNotNone(user)
    
    def test_user_register_duplicate(self):
        # Test registering duplicate user
        output, result = self.capture_output(self.user_manager.register, 'admin', 'newpassword', 'admin')
        self.assertFalse(result)
        self.assertIn("Username already exists", output)
    
    def test_user_register_invalid_role(self):
        # Test registering with invalid role
        output, result = self.capture_output(self.user_manager.register, 'invalidroleuser', 'password', 'invalid_role')
        self.assertFalse(result)
        self.assertIn("Role 'invalid_role' does not exist", output)
    
    def test_list_users(self):
        # Test listing all usersxists by creating it
        self.user_manager.authenticate('admin', 'admin123')  # Login as admin
        self.user_manager.register('newuser_for_listing', 'password123', 'user')
        
        # Test listing all users
        output, result = self.capture_output(self.user_manager.list_users)
        self.assertTrue(result)
        self.assertIn("admin", output)
        self.assertIn("testuser", output)
        # Check for the user we just created instead of "newuser"
        self.assertIn("newuser_for_listing", output)
    
    def test_help_not_logged_in(self):
        # Test help when not logged in
        self.user_manager.logout()
        output, result = self.capture_output(self.user_manager.help, 'user', {})
        self.assertTrue(result)
        self.assertIn("Available commands", output)
        self.assertIn("login", output)
    
    def test_delete_user_success(self):
        # Add a test user
        self.cursor.execute("INSERT INTO User (username, password) VALUES ('deleteuser', 'password123')")
        self.cursor.execute("INSERT INTO user_role (username, role_id) VALUES ('deleteuser', 2)")
        self.conn.commit()

        # Test deleting the user
        output, result = self.capture_output(self.user_manager.delete_user, 'deleteuser')
        self.assertTrue(result)
        self.assertIn("User 'deleteuser' and all related data have been deleted successfully.", output)

        # Verify user was deleted
        self.cursor.execute("SELECT * FROM User WHERE username = 'deleteuser'")
        user = self.cursor.fetchone()
        self.assertIsNone(user)

    def test_delete_user_nonexistent(self):
        # Test deleting a non-existent user
        output, result = self.capture_output(self.user_manager.delete_user, 'nonexistentuser')
        self.assertFalse(result)
        self.assertIn("Error: User 'nonexistentuser' does not exist.", output)

    # ============= CATEGORY MANAGER TESTS =============
    
    def test_add_category_success(self):
        # Test adding a new category
        output, result = self.capture_output(self.category_manager.add_category, 'electronics')
        self.assertTrue(result)
        self.assertIn("added successfully", output)
        
        # Verify category was added
        self.cursor.execute("SELECT category_name FROM Categories WHERE category_name = ?", ('electronics',))
        category = self.cursor.fetchone()
        self.assertIsNotNone(category)
    
    def test_add_category_duplicate(self):
        # Test adding a duplicate category
        output, result = self.capture_output(self.category_manager.add_category, 'food')
        self.assertFalse(result)
        self.assertIn("already exists", output)
    
    def test_add_category_whitespace(self):
        # Test adding category with whitespace (should be trimmed)
        output, result = self.capture_output(self.category_manager.add_category, '  entertainment  ')
        self.assertTrue(result)
        
        # Verify category was added with trimmed name
        self.cursor.execute("SELECT category_name FROM Categories WHERE category_name = ?", ('entertainment',))
        category = self.cursor.fetchone()
        self.assertIsNotNone(category)
    
    def test_add_category_empty(self):
        # Test adding empty category
        output, result = self.capture_output(self.category_manager.add_category, '')
        self.assertFalse(result)
        # Update expected error message to match actual implementation
        self.assertIn("Category name cannot be empty", output)
    
    def test_list_categories(self):
        # Test listing categories
        output, result = self.capture_output(self.category_manager.list_categories)
        self.assertTrue(result)
        self.assertIn('food', output)
        self.assertIn('rent', output)
        self.assertIn('electronics', output)
        self.assertIn('entertainment', output)
    
    def test_delete_category_success(self):
        # Add a test category
        self.cursor.execute("INSERT INTO Categories (category_name) VALUES ('testcategory')")
        self.conn.commit()

        # Test deleting the category
        output, result = self.capture_output(self.category_manager.delete_category, 'testcategory')
        self.assertTrue(result)
        self.assertIn("Category 'testcategory' and all related data have been deleted successfully.", output)

        # Verify category was deleted
        self.cursor.execute("SELECT * FROM Categories WHERE category_name = 'testcategory'")
        category = self.cursor.fetchone()
        self.assertIsNone(category)

    def test_delete_category_nonexistent(self):
        # Test deleting a non-existent category
        output, result = self.capture_output(self.category_manager.delete_category, 'nonexistentcategory')
        self.assertFalse(result)
        self.assertIn("Error: Category 'nonexistentcategory' does not exist.", output)

    # ============= PAYMENT MANAGER TESTS =============
    
    def test_add_payment_method_success(self):
        # Test adding a new payment method
        output, result = self.capture_output(self.payment_manager.add_payment_method, 'debit_card')
        self.assertTrue(result)
        self.assertIn("added successfully", output)
        
        # Verify payment method was added
        self.cursor.execute("SELECT payment_method_name FROM Payment_Method WHERE payment_method_name = ?", ('debit_card',))
        method = self.cursor.fetchone()
        self.assertIsNotNone(method)
    
    def test_add_payment_method_duplicate(self):
        # Test adding a duplicate payment method
        output, result = self.capture_output(self.payment_manager.add_payment_method, 'cash')
        self.assertFalse(result)
        self.assertIn("already exists", output)
    
    def test_add_payment_method_whitespace(self):
        # Test adding payment method with whitespace
        output, result = self.capture_output(self.payment_manager.add_payment_method, '  paypal  ')
        self.assertTrue(result)
        
        # Verify payment method was added with trimmed name
        self.cursor.execute("SELECT payment_method_name FROM Payment_Method WHERE payment_method_name = ?", ('paypal',))
        method = self.cursor.fetchone()
        self.assertIsNotNone(method)
    
    def test_list_payment_methods(self):
        # Test listing payment methods
        output, result = self.capture_output(self.payment_manager.list_payment_methods)
        self.assertTrue(result)
        self.assertIn('cash', output)
        self.assertIn('credit_card', output)
        self.assertIn('debit_card', output)
        self.assertIn('paypal', output)
    
    # ============= EXPENSE MANAGER TESTS =============
    
    def test_add_expense_success(self):
        # Login as a user
        self.user_manager.authenticate('admin', 'admin123')
        self.expense_manager.set_current_user('admin')
        
        # Test adding a valid expense
        output, result = self.capture_output(
            self.expense_manager.addexpense,
            amount='50.25',
            category='food',
            payment_method='cash',
            date='2023-06-15',
            description='Grocery shopping',
            tag='groceries'
        )
        self.assertTrue(result)
        self.assertIn("Expense Added Successfully", output)
        
        # Verify expense was added
        self.cursor.execute("SELECT amount FROM Expense WHERE amount = 50.25")
        expense = self.cursor.fetchone()
        self.assertIsNotNone(expense)
    
    def test_add_expense_invalid_amount(self):
        # Test adding expense with invalid amount
        output, result = self.capture_output(
            self.expense_manager.addexpense,
            amount='not_a_number',
            category='food',
            payment_method='cash',
            date='2023-06-15',
            description='Grocery shopping',
            tag='groceries'
        )
        self.assertFalse(result)
        self.assertIn("Invalid amount", output)
    
    def test_add_expense_invalid_category(self):
        # Test adding expense with non-existent category
        output, result = self.capture_output(
            self.expense_manager.addexpense,
            amount='30.00',
            category='non_existent_category',
            payment_method='cash',
            date='2023-06-15',
            description='Test expense',
            tag='test'
        )
        self.assertFalse(result)
        self.assertIn("Category 'non_existent_category' does not exist", output)
    
    def test_add_expense_invalid_payment_method(self):
        # Test adding expense with non-existent payment method
        output, result = self.capture_output(
            self.expense_manager.addexpense,
            amount='30.00',
            category='food',
            payment_method='non_existent_method',
            date='2023-06-15',
            description='Test expense',
            tag='test'
        )
        self.assertFalse(result)
        self.assertIn("Payment Method 'non_existent_method' does not exist", output)
    
    def test_add_expense_zero_amount(self):
        # Test adding expense with zero amount (should be valid)
        output, result = self.capture_output(
            self.expense_manager.addexpense,
            amount='0',
            category='food',
            payment_method='cash',
            date='2023-06-15',
            description='Free item',
            tag='free'
        )
        self.assertTrue(result)
        self.assertIn("Expense Added Successfully", output)
    
    def test_add_expense_negative_amount(self):
        # Test adding expense with negative amount (could be refund)
        output, result = self.capture_output(
            self.expense_manager.addexpense,
            amount='-25.50',
            category='food',
            payment_method='cash',
            date='2023-06-15',
            description='Refund',
            tag='refund'
        )
        self.assertTrue(result)
        self.assertIn("Expense Added Successfully", output)
    
    def test_add_expense_empty_description(self):
        # Test adding expense with empty description
        output, result = self.capture_output(
            self.expense_manager.addexpense,
            amount='15.00',
            category='food',
            payment_method='cash',
            date='2023-06-15',
            description='',
            tag='misc'
        )
        self.assertTrue(result)
        self.assertIn("Expense Added Successfully", output)
    
    def test_update_expense_success(self):
        # First add an expense
        self.expense_manager.addexpense(
            amount='100.00',
            category='food',
            payment_method='cash',
            date='2023-06-15',
            description='Test for update',
            tag='test'
        )
        
        # Get the expense ID
        self.cursor.execute("SELECT expense_id FROM Expense WHERE description = 'Test for update'")
        expense_id = self.cursor.fetchone()[0]
        
        # Test updating the expense amount
        output, result = self.capture_output(self.expense_manager.update_expense, expense_id, 'amount', '150.00')
        self.assertTrue(result)
        self.assertIn("updated successfully", output)
        
        # Verify update
        self.cursor.execute("SELECT amount FROM Expense WHERE expense_id = ?", (expense_id,))
        updated_amount = self.cursor.fetchone()[0]
        self.assertEqual(updated_amount, 150.00)
    
    def test_update_expense_description(self):
        # First add an expense
        self.expense_manager.addexpense(
            amount='100.00',
            category='food',
            payment_method='cash',
            date='2023-06-15',
            description='Original description',
            tag='test'
        )
        
        # Get the expense ID
        self.cursor.execute("SELECT expense_id FROM Expense WHERE description = 'Original description'")
        expense_id = self.cursor.fetchone()[0]
        
        # Test updating the description
        output, result = self.capture_output(self.expense_manager.update_expense, expense_id, 'description', 'Updated description')
        self.assertTrue(result)
        
        # Verify update
        self.cursor.execute("SELECT description FROM Expense WHERE expense_id = ?", (expense_id,))
        updated_desc = self.cursor.fetchone()[0]
        self.assertEqual(updated_desc, 'Updated description')
    
    def test_update_expense_date(self):
        # First add an expense
        self.expense_manager.addexpense(
            amount='100.00',
            category='food',
            payment_method='cash',
            date='2023-06-15',
            description='Date test',
            tag='test'
        )
        
        # Get the expense ID
        self.cursor.execute("SELECT expense_id FROM Expense WHERE description = 'Date test'")
        expense_id = self.cursor.fetchone()[0]
        
        # Test updating the date
        output, result = self.capture_output(self.expense_manager.update_expense, expense_id, 'date', '2023-07-01')
        self.assertTrue(result)
        
        # Verify update
        self.cursor.execute("SELECT date FROM Expense WHERE expense_id = ?", (expense_id,))
        updated_date = self.cursor.fetchone()[0]
        self.assertEqual(updated_date, '2023-07-01')
    
    def test_update_expense_nonexistent(self):
        # Test updating a non-existent expense
        output, result = self.capture_output(self.expense_manager.update_expense, 9999, 'amount', '150.00')
        self.assertFalse(result)
        self.assertIn("doesn't exist", output)
    
    def test_update_expense_invalid_field(self):
        # First add an expense
        self.expense_manager.addexpense(
            amount='100.00',
            category='food',
            payment_method='cash',
            date='2023-06-15',
            description='Invalid field test',
            tag='test'
        )
        
        # Get the expense ID
        self.cursor.execute("SELECT expense_id FROM Expense WHERE description = 'Invalid field test'")
        expense_id = self.cursor.fetchone()[0]
        
        # Test updating an invalid field
        output, result = self.capture_output(self.expense_manager.update_expense, expense_id, 'invalid_field', 'new_value')
        self.assertFalse(result)
        self.assertIn("not valid for updating", output)
    
    def test_delete_expense_success(self):
        # First add an expense
        self.expense_manager.addexpense(
            amount='100.00',
            category='food',
            payment_method='cash',
            date='2023-06-15',
            description='Test for delete',
            tag='test'
        )
        
        # Get the expense ID
        self.cursor.execute("SELECT expense_id FROM Expense WHERE description = 'Test for delete'")
        expense_id = self.cursor.fetchone()[0]
        
        # Test deleting the expense
        output, result = self.capture_output(self.expense_manager.delete_expense, expense_id)
        self.assertTrue(result)
        self.assertIn("deleted successfully", output)
        
        # Verify deletion
        self.cursor.execute("SELECT * FROM Expense WHERE expense_id = ?", (expense_id,))
        deleted_expense = self.cursor.fetchone()
        self.assertIsNone(deleted_expense)
    
    def test_delete_expense_nonexistent(self):
        # Test deleting a non-existent expense
        output, result = self.capture_output(self.expense_manager.delete_expense, 9999)
        self.assertFalse(result)
        self.assertIn("doesn't exist", output)
    
    def test_list_expenses_no_filter(self):
        # Add some test expenses first
        self.expense_manager.addexpense('25.00', 'food', 'cash', '2023-06-10', 'Lunch', 'meal')
        self.expense_manager.addexpense('150.00', 'rent', 'credit_card', '2023-06-01', 'Monthly rent', 'housing')
        
        # Test listing all expenses (user_role='admin' shows all expenses)
        output, _ = self.capture_output(self.expense_manager.list_expenses, user_role='admin')
        self.assertIn('Lunch', output)
        self.assertIn('Monthly rent', output)
        self.assertIn('25.00', output)
        self.assertIn('150.00', output)
    
    def test_list_expenses_with_amount_filter(self):
        # Add test expenses if not already added
        self.expense_manager.addexpense('25.00', 'food', 'cash', '2023-06-10', 'Lunch', 'meal')
        self.expense_manager.addexpense('150.00', 'rent', 'credit_card', '2023-06-01', 'Monthly rent', 'housing')
        
        # Test listing expenses with amount filter
        filters = {'amount': [['>','100.00']]}
        output, _ = self.capture_output(self.expense_manager.list_expenses, filters, 'admin')
        self.assertIn('Monthly rent', output)
        self.assertIn('150.00', output)
        self.assertNotIn('Lunch', output)  # Should be filtered out
    
    def test_list_expenses_with_category_filter(self):
        # Test listing expenses with category filter
        filters = {'category': [['=', 'food']]}
        output, _ = self.capture_output(self.expense_manager.list_expenses, filters, 'admin')
        self.assertIn('Lunch', output)
        self.assertNotIn('Monthly rent', output)  # Should be filtered out
    
    def test_list_expenses_with_multiple_filters(self):
        # Test listing expenses with multiple filters
        filters = {
            'amount': [['>','10.00']],
            'category': [['=', 'food']]
        }
        output, _ = self.capture_output(self.expense_manager.list_expenses, filters, 'admin')
        self.assertIn('Lunch', output)
        self.assertNotIn('Monthly rent', output)  # Should be filtered out
    
    def test_list_expenses_no_results(self):
        # Test with filters that match no expenses
        filters = {'amount': [['>','1000.00']]}
        output, _ = self.capture_output(self.expense_manager.list_expenses, filters, 'admin')
        self.assertIn('No expenses found', output)
    
    # ============= CSV OPERATIONS TESTS =============
    
    def test_export_csv(self):
        # Add some test expenses first
        self.expense_manager.addexpense('35.00', 'food', 'cash', '2023-06-20', 'Dinner', 'meal')
        
        # Set up a test file path
        test_export_path = os.path.join(self.temp_dir, 'test_export.csv')
        
        # Test exporting to CSV
        self.csv_operations.set_current_user('admin')
        output, result = self.capture_output(self.csv_operations.export_csv, test_export_path)
        self.assertTrue(result)
        self.assertIn(f"Expenses exported successfully to {test_export_path}", output)
        
        # Verify file was created
        self.assertTrue(os.path.exists(test_export_path))
        
        # Verify file content
        with open(test_export_path, 'r') as f:
            content = f.read()
            self.assertIn('amount,category,payment_method,date,description,tag', content)
            self.assertIn('Dinner', content)
    
    def test_export_csv_with_sorting(self):
        # Add some test expenses with different amounts
        self.expense_manager.addexpense('35.00', 'food', 'cash', '2023-06-20', 'Dinner', 'meal')
        self.expense_manager.addexpense('15.00', 'food', 'cash', '2023-06-21', 'Breakfast', 'meal')
        
        # Set up a test file path
        test_export_path = os.path.join(self.temp_dir, 'test_export_sorted.csv')
        
        # Test exporting to CSV with sorting
        output, result = self.capture_output(self.csv_operations.export_csv, test_export_path, 'amount')
        self.assertTrue(result)
        
        # Read the file and check if amounts are in expected order
        with open(test_export_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header
            rows = list(reader)
            # With ORDER BY, smallest amount should come first
            self.assertLess(float(rows[0][0]), float(rows[1][0]))
    
    def test_export_csv_invalid_sort_field(self):
        # Test export with invalid sort field
        test_export_path = os.path.join(self.temp_dir, 'test_export_invalid.csv')
        output, result = self.capture_output(self.csv_operations.export_csv, test_export_path, 'invalid_field')
        self.assertFalse(result)
        self.assertIn("Invalid sort field", output)
    
    def test_import_csv_valid(self):
        # Create a valid test CSV file
        test_import_path = os.path.join(self.temp_dir, 'test_import.csv')
        with open(test_import_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['amount', 'category', 'payment_method', 'date', 'description', 'tag', 'payment_detail_identifier'])
            writer.writerow(['50.00', 'food', 'cash', '2023-07-01', 'Imported lunch', 'meal', ''])
        
        # Test importing from CSV
        self.csv_operations.set_current_user('admin')
        output, result = self.capture_output(self.csv_operations.import_expenses, test_import_path)
        self.assertTrue(result)
        
        # Verify expense was imported
        self.cursor.execute("SELECT description FROM Expense WHERE description = 'Imported lunch'")
        imported = self.cursor.fetchone()
        self.assertIsNotNone(imported)
    
    def test_import_csv_invalid_header(self):
        # Create a CSV file with invalid header
        test_import_path = os.path.join(self.temp_dir, 'test_import_invalid.csv')
        with open(test_import_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['wrong', 'header', 'format'])
            writer.writerow(['50.00', 'food', 'cash'])
        
        # Test importing from invalid CSV
        output, result = self.capture_output(self.csv_operations.import_expenses, test_import_path)
        self.assertFalse(result)
        self.assertIn("Error: CSV header does not match", output)
    
    def test_import_csv_nonexistent_file(self):
        # Test importing from a non-existent file
        output, result = self.capture_output(self.csv_operations.import_expenses, 'nonexistent_file.csv')
        self.assertFalse(result)
        self.assertIn("not found", output)
    
    def test_import_csv_duplicate_entries(self):
        # Create a CSV with duplicate entries
        test_import_path = os.path.join(self.temp_dir, 'test_import_duplicates.csv')
        with open(test_import_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['amount', 'category', 'payment_method', 'date', 'description', 'tag', 'payment_detail_identifier'])
            writer.writerow(['50.00', 'food', 'cash', '2023-07-01', 'Duplicate entry', 'meal', ''])
            writer.writerow(['50.00', 'food', 'cash', '2023-07-01', 'Duplicate entry', 'meal', ''])
        
        # Test importing
        output, result = self.capture_output(self.csv_operations.import_expenses, test_import_path)
        self.assertTrue(result)
        self.assertIn("Import completed: 2 expenses added successfully, 0 duplicates skipped, 0 errors.", output)
    
    # ============= REPORTING TESTS =============
    # High amount to ensure it appears in top 3
    # Note: For reporting tests, we'll primarily check function arguments and output textdphones', 'gadget')
    # since the visual elements would be handled by matplotlib    
    def test_report_top_expenses_invalid_n(self):
        # Test with invalid N parameter
        self.report_manager.set_user_info('admin', 'admin')
        with patch('matplotlib.pyplot.show'), patch('matplotlib.pyplot.pause'):
            output, _ = self.capture_output(
                self.report_manager.generate_report_top_expenses, 
                '-1', '2023-01-01', '2023-12-31'
            )
            self.assertIn('N must be a positive integer', output)
    
    def test_report_top_expenses_invalid_date(self):
        # Test with invalid date format
        self.report_manager.set_user_info('admin', 'admin')
        with patch('matplotlib.pyplot.show'), patch('matplotlib.pyplot.pause'):
            output, _ = self.capture_output(
                self.report_manager.generate_report_top_expenses, 
                '3', '01/01/2023', '2023-12-31'
            )
            self.assertIn('Dates must be in the format YYYY-MM-DD', output)
    
    def test_report_category_spending(self):
        # Set up test data for reports
        self.expense_manager.addexpense('45.00', 'food', 'cash', '2023-07-15', 'More food', 'meal')
        
        # Set up report manager with user info
        self.report_manager.set_user_info('admin', 'admin')
        
        # Mock plt.show() to prevent display during tests
        with patch('matplotlib.pyplot.show'), patch('matplotlib.pyplot.pause'):
            # Test generating category spending report
            output, _ = self.capture_output(
                self.report_manager.generate_report_category_spending, 
                'food'
            )
            self.assertIn('Summary Statistics for Category', output)
            self.assertIn('food', output)
            self.assertIn('Total spending', output)
    
    def test_report_category_spending_nonexistent(self):
        # Test generating report for non-existent category
        self.report_manager.set_user_info('admin', 'admin')
        output, _ = self.capture_output(
            self.report_manager.generate_report_category_spending, 
            'nonexistent'
        )
        self.assertIn('does not exist', output)
    
    def test_report_payment_method_usage(self):
        # Add test data
        self.expense_manager.addexpense('60.00', 'food', 'credit_card', '2023-07-20', 'Card payment', 'meal')
        
        # Set up report manager
        self.report_manager.set_user_info('admin', 'admin')
        
        # Test report generation
        with patch('matplotlib.pyplot.show'), patch('matplotlib.pyplot.pause'):
            output, _ = self.capture_output(
                self.report_manager.generate_report_payment_method_usage
            )
            self.assertIn('Payment Method Usage Report', output)
            self.assertIn('credit_card', output)
    
    def test_report_frequent_category(self):
        # Add test data with multiple categories
        self.expense_manager.addexpense('20.00', 'food', 'cash', '2023-07-21', 'Food 1', 'meal')
        self.expense_manager.addexpense('30.00', 'food', 'cash', '2023-07-22', 'Food 2', 'meal')
        self.expense_manager.addexpense('40.00', 'electronics', 'credit_card', '2023-07-23', 'Electronics', 'gadget')
        
        # Set up report manager
        self.report_manager.set_user_info('admin', 'admin')
        
        # Test report generation
        with patch('matplotlib.pyplot.show'), patch('matplotlib.pyplot.pause'):
            output, _ = self.capture_output(
                self.report_manager.generate_report_frequent_category
            )
            self.assertIn('Category Usage Report', output)
            self.assertIn('Most frequently used category', output)
            # Food should have most entries (3)
            self.assertIn('food', output)

    def test_report_monthly_category_spending(self):
        # Add test data spanning multiple months
        self.expense_manager.addexpense('50.00', 'food', 'cash', '2023-06-15', 'June food', 'meal')
        self.expense_manager.addexpense('75.00', 'food', 'cash', '2023-07-15', 'July food', 'meal')
        self.expense_manager.addexpense('100.00', 'rent', 'credit_card', '2023-07-01', 'July rent', 'housing')
        
        # Set up report manager
        self.report_manager.set_user_info('admin', 'admin')
        
        # Test report generation
        with patch('matplotlib.pyplot.show'), patch('matplotlib.pyplot.pause'):
            output, _ = self.capture_output(
                self.report_manager.generate_report_monthly_category_spending
            )
            self.assertIn('Monthly Category Spending Report', output)
            self.assertIn('2023-06', output)  # June data
            self.assertIn('2023-07', output)  # July data
    
    def test_report_above_average_expenses(self):
        # Add test data with varying amounts in same category
        self.expense_manager.addexpense('10.00', 'food', 'cash', '2023-08-01', 'Small meal', 'meal')
        self.expense_manager.addexpense('50.00', 'food', 'cash', '2023-08-02', 'Average meal', 'meal')
        self.expense_manager.addexpense('100.00', 'food', 'cash', '2023-08-03', 'Expensive meal', 'meal')
        
        # Set up report manager
        self.report_manager.set_user_info('admin', 'admin')
        
        # Test report generation
        with patch('matplotlib.pyplot.show'), patch('matplotlib.pyplot.pause'):
            output, _ = self.capture_output(
                self.report_manager.generate_report_above_average_expenses
            )
            self.assertIn('Expenses Above Category Average', output)
            self.assertIn('Expensive meal', output)  # Should be above average
            self.assertNotIn('Small meal', output)  # Should be below average
    
    def test_report_tag_expenses(self):
        # Add test data with different tags
        self.expense_manager.addexpense('25.00', 'food', 'cash', '2023-08-10', 'Lunch', 'lunch')
        self.expense_manager.addexpense('35.00', 'food', 'cash', '2023-08-11', 'Dinner', 'dinner')
        
        # Set up report manager
        self.report_manager.set_user_info('admin', 'admin')
        
        # Test report generation
        with patch('matplotlib.pyplot.show'), patch('matplotlib.pyplot.pause'):
            output, _ = self.capture_output(
                self.report_manager.generate_report_tag_expenses
            )
            self.assertIn('Tag Usage Report', output)
            self.assertIn('lunch', output)
            self.assertIn('dinner', output)
    
    def test_report_highest_spender_per_month(self):
        # Create another test user
        self.user_manager.register('testuser2', 'password456', 'user')
        
        # Add test data with different users
        # First user's expenses
        self.expense_manager.set_current_user('admin')
        self.expense_manager.addexpense('200.00', 'rent', 'credit_card', '2023-09-01', 'Admin Sept rent', 'housing')
        
        # Second user's expenses
        self.expense_manager.set_current_user('testuser')
        self.expense_manager.addexpense('300.00', 'rent', 'credit_card', '2023-09-02', 'User Sept rent', 'housing')
        
        # Third user's expenses
        self.expense_manager.set_current_user('testuser2')
        self.expense_manager.addexpense('100.00', 'rent', 'credit_card', '2023-09-03', 'User2 Sept rent', 'housing')
        
        # Return to admin for report
        self.expense_manager.set_current_user('admin')
        self.report_manager.set_user_info('admin', 'admin')
        
        # Test report generation (admin only report)
        with patch('matplotlib.pyplot.show'), patch('matplotlib.pyplot.pause'):
            output, _ = self.capture_output(
                self.report_manager.generate_report_highest_spender_per_month
            )
            self.assertIn('Highest Spender per Month', output)
            self.assertIn('2023-09', output)  # September data
            self.assertIn('testuser', output)  # Should be the highest spender
    
    def test_report_payment_method_details_expense(self):
        # Add expense with payment detail
        self.expense_manager.set_current_user('admin')
        self.expense_manager.addexpense(
            amount='120.00',
            category='electronics',
            payment_method='credit_card',
            date='2023-09-15',
            description='Phone charger',
            tag='gadget',
            payment_detail_identifier='1234567890123456'
        )
        
        # Set up report manager
        self.report_manager.set_user_info('admin', 'admin')
        
        # Test report generation
        with patch('matplotlib.pyplot.show'), patch('matplotlib.pyplot.pause'):
            output, _ = self.capture_output(
                self.report_manager.generate_report_payment_method_details_expense
            )
            self.assertIn('Payment Method Details Usage Report', output)
            # Check for masked payment details (should not show full number)
            self.assertNotIn('1234567890123456', output)
            # But should see masked version
            self.assertIn('12************56', output)
    
    def test_report_analyze_expenses(self):
        # Add more test data if needed
        self.expense_manager.set_current_user('admin')
        self.expense_manager.addexpense('45.00', 'food', 'cash', '2023-10-01', 'October food', 'meal')
        self.expense_manager.addexpense('55.00', 'entertainment', 'credit_card', '2023-10-05', 'Movie tickets', 'fun')
        
        # Set up report manager
        self.report_manager.set_user_info('admin', 'admin')
        
        # Test report generation with no filters
        with patch('matplotlib.pyplot.show'), patch('matplotlib.pyplot.pause'):
            output, _ = self.capture_output(
                self.report_manager.generate_expenses_analytics
            )
            self.assertIn('Expense Analytics Dashboard', output)
            self.assertIn('Total expenses found:', output)
    
    def test_report_analyze_expenses_with_filters(self):
        # Set up report manager
        self.report_manager.set_user_info('admin', 'admin')
        
        # Test report generation with filters
        filters = {'category': [['=', 'food']]}
        with patch('matplotlib.pyplot.show'), patch('matplotlib.pyplot.pause'):
            output, _ = self.capture_output(
                self.report_manager.generate_expenses_analytics, filters
            )
            self.assertIn('Expense Analytics Dashboard', output)
            # Should show smaller count than the unfiltered report
            self.assertIn('Total expenses found:', output)

if __name__ == '__main__':
    unittest.main()
