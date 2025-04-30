import sqlite3
from expense_tracker.database.sql_queries import CATEGORY_QUERIES

class CategoryManager:
    def __init__(self, cursor, conn):
        self.conn = conn
        self.cursor = cursor
    
    def add_category(self, category_name):
        category_name = category_name.strip().lower()
        
        if not category_name:
            print("Category name cannot be empty.")
            return False
        
        try:
            self.cursor.execute(CATEGORY_QUERIES["add_category"], (category_name,))
            self.conn.commit()
            print(f"Category '{category_name}' added successfully.")
            return True
        except sqlite3.IntegrityError:
            print(f"Error: Category '{category_name}' already exists.")
            return False
    
    def list_categories(self):
        self.cursor.execute(CATEGORY_QUERIES["list_categories"])
        categories = self.cursor.fetchall()

        if not categories:
            print("No categories found.")
        else:
            print("Categories:")
            print("-" * 20)
            for category in categories:
                print(f"- {category[0]}")
        return True

    def delete_category(self, category_name):
        """Deletes a category and all related data."""
        try:
            # Check if category exists
            self.cursor.execute("SELECT category_id FROM Categories WHERE category_name = ?", (category_name,))
            if not self.cursor.fetchone():
                print(f"Error: Category '{category_name}' does not exist.")
                return False

            # Check if the category has expenses associated with it
            self.cursor.execute(CATEGORY_QUERIES["check_category_expenses"], (category_name,))
            expense_count = self.cursor.fetchone()[0]
            if expense_count > 0:
                print(f"Error: Cannot delete category '{category_name}' as it has {expense_count} expenses associated with it.")
                print("Please reassign or delete all expenses in this category first.")
                return False

            # Delete category-related data
            self.cursor.execute(CATEGORY_QUERIES["delete_category_related"], (category_name,))
            
            # Delete the category
            self.cursor.execute(CATEGORY_QUERIES["delete_category"], (category_name,))
            self.conn.commit()
            print(f"Category '{category_name}' has been deleted successfully.")
            return True
        except sqlite3.Error as e:
            print(f"Error: Unable to delete category '{category_name}'. {e}")
            return False