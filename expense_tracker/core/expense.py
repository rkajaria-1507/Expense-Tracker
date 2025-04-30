import sqlite3
from datetime import datetime
from expense_tracker.database.sql_queries import EXPENSE_QUERIES, BASE_EXPENSE_QUERY

class ExpenseManager:
    def __init__(self, cursor, conn):
        self.conn = conn
        self.cursor = cursor
        self.current_user = None
    
    def set_current_user(self, username):
        self.current_user = username
    
    def _validate_date(self, date_str):
        """Validate that a date string is in YYYY-MM-DD format and is a valid date"""
        try:
            # Try to parse the date string
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    # ...existing code...
    
    def addexpense(self, amount, category, payment_method, date, description, tag, payment_detail_identifier="", import_fn=0):
        # Try to convert amount to float
        try:
            amount = float(amount)
        except ValueError:
            print(f"Error: Invalid amount '{amount}'. Must be a number.")
            return False
        
        # Validate date format
        if not self._validate_date(date):
            print(f"Error: Invalid date format '{date}'. Must be in YYYY-MM-DD format.")
            return False
        
        try:
            self.cursor.execute(EXPENSE_QUERIES["insert_expense"], (date, amount, description))
            expense_id = self.cursor.lastrowid
            
            # Check if category exists
            self.cursor.execute("SELECT category_id FROM Categories WHERE category_name = ?", (category,))
            result = self.cursor.fetchone()
            if result is None:
                print(f"Error: Category '{category}' does not exist. Adding failed!")
                self.conn.rollback()
                return False
            
            category_id = result[0]  # Extract category_id
            self.cursor.execute(EXPENSE_QUERIES["insert_category_expense"], (category_id, expense_id))
            
            self.cursor.execute("SELECT tag_id FROM Tags WHERE tag_name = ?", (tag,))
            result = self.cursor.fetchone()
            if result is None:
                self.cursor.execute(EXPENSE_QUERIES["insert_tag"], (tag,))
                tag_id = self.cursor.lastrowid
            else:
                tag_id = result[0]
                
            self.cursor.execute(EXPENSE_QUERIES["insert_tag_expense"], (tag_id, expense_id))
            
            self.cursor.execute("SELECT payment_method_id FROM Payment_Method WHERE Payment_Method_Name = ?", (payment_method,))
            result = self.cursor.fetchone()
            if result is None:
                print(f"Error: Payment Method '{payment_method}' does not exist. Adding failed!")
                self.conn.rollback()
                return False
            
            payment_method_id = result[0]  # Extract payment_method_id
            self.cursor.execute(EXPENSE_QUERIES["insert_payment_method_expense"], 
                               (payment_method_id, expense_id, payment_detail_identifier))
            
            self.cursor.execute(EXPENSE_QUERIES["insert_user_expense"], (self.current_user, expense_id))
            
            self.conn.commit()
            if import_fn == 0:
                print("Expense Added Successfully")
            return True
            
        except sqlite3.Error as e:
            print(f"Database error adding expense: {e}")
            self.conn.rollback()
            return False
    
    def update_expense(self, expense_id, field, new_value):
        self.cursor.execute(EXPENSE_QUERIES["check_expense_owner"], (expense_id, self.current_user))
        exists = self.cursor.fetchone()[0] > 0  # True if count > 0, else False
        if not exists:
            print(f"Error: Expense ID {expense_id} doesn't exist or doesn't belong to the current user.")
            return False

        field = field.lower()

        try:
            if field == 'amount':
                try:
                    amount = float(new_value)
                    self.cursor.execute(EXPENSE_QUERIES["update_expense_amount"], (amount, expense_id))
                except ValueError:
                    print(f"Error: Invalid amount '{new_value}'. Must be a number.")
                    return False
            elif field == 'description':
                self.cursor.execute(EXPENSE_QUERIES["update_expense_description"], (new_value, expense_id))
            elif field == 'date':
                # Validate date format before updating
                if not self._validate_date(new_value):
                    print(f"Error: Invalid date format '{new_value}'. Must be in YYYY-MM-DD format.")
                    return False
                self.cursor.execute(EXPENSE_QUERIES["update_expense_date"], (new_value, expense_id))
            elif field == 'category':
                self.cursor.execute("SELECT category_id FROM Categories WHERE category_name = ?", (new_value,))
                category = self.cursor.fetchone()
                if category is None:
                    print(f"Error: Category '{new_value}' does not exist.")
                    return False
                category_id = category[0]
                self.cursor.execute(EXPENSE_QUERIES["update_category_expense"], (category_id, expense_id))
            elif field == 'tag':
                self.cursor.execute("SELECT tag_id FROM Tags WHERE tag_name = ?", (new_value,))
                tag = self.cursor.fetchone()
                if tag is None:
                    self.cursor.execute(EXPENSE_QUERIES["insert_tag"], (new_value,))
                    tag_id = self.cursor.lastrowid
                else:
                    tag_id = tag[0]
                self.cursor.execute(EXPENSE_QUERIES["update_tag_expense"], (tag_id, expense_id))
            elif field == 'payment_method':
                self.cursor.execute("SELECT payment_method_id FROM Payment_Method WHERE payment_method_name = ?", (new_value,))
                payment_method = self.cursor.fetchone()
                if payment_method is None:
                    print(f"Error: Payment Method '{new_value}' doesn't exist.")
                    return False
                payment_method_id = payment_method[0]
                self.cursor.execute(EXPENSE_QUERIES["update_payment_method_expense"], (payment_method_id, expense_id))
            else:
                print(f"Error: Field '{field}' is not valid for updating.")
                return False

            self.conn.commit()
            print(f"Expense ID {expense_id} updated successfully.")
            return True
        except sqlite3.Error as e:
            print(f"Error: Failed to update expense. {e}")
            return False
    
    def delete_expense(self, expense_id):
        self.cursor.execute(EXPENSE_QUERIES["check_expense_owner"], (expense_id, self.current_user))
        exists = self.cursor.fetchone()[0] > 0  # True if count > 0, else False
        if not exists:
            print(f"Error: Expense ID {expense_id} doesn't exist or doesn't belong to the current user.")
            return False

        try:
            # Delete from related tables
            self.cursor.execute(EXPENSE_QUERIES["delete_category_expense"], (expense_id,))
            self.cursor.execute(EXPENSE_QUERIES["delete_tag_expense"], (expense_id,))
            self.cursor.execute(EXPENSE_QUERIES["delete_payment_method_expense"], (expense_id,))
            self.cursor.execute(EXPENSE_QUERIES["delete_user_expense"], (expense_id,))
            
            # Delete from the main Expense table
            self.cursor.execute(EXPENSE_QUERIES["delete_expense"], (expense_id,))
            
            self.conn.commit()
            print(f"Expense ID {expense_id} deleted successfully.")
            return True
        except sqlite3.Error as e:
            print(f"Error: Failed to delete expense. {e}")
            return False
    
    def list_expenses(self, filters={}, user_role=None):
        try:
            # Start with base query
            query = BASE_EXPENSE_QUERY
            params = []
            
            # Check if current user is admin or regular user
            if user_role != "admin":
                # Regular user can only see their own expenses
                query += """
                WHERE e.expense_id IN (
                    SELECT expense_id FROM user_expense WHERE username = ?
                )
                """
                params.append(self.current_user)
            
            # Define operation fields
            op_fields = {"and": ["amount", "date"], 
                        "or": ["category", "tag", "payment_method", "month"]}
            
            # Month name to number mapping
            month_mapping = {
                "january": "01", "february": "02", "march": "03", "april": "04",
                "may": "05", "june": "06", "july": "07", "august": "08",
                "september": "09", "october": "10", "november": "11", "december": "12"
            }
            
            # Process filters
            for field in filters:
                if not filters[field]:  # Skip empty filter lists
                    continue
                    
                if field in op_fields["and"]:
                    op = "AND"
                else:
                    op = "OR"
                    
                # Special handling for month
                if field == "month":
                    connector = "WHERE" if "WHERE" not in query else "AND"
                    query += f" {connector} ("
                    first = True
                    for constraint in filters[field]:
                        op_type, value = constraint
                        if not first:
                            query += f" {op} "
                        first = False
                        
                        # Handle month name conversion
                        if isinstance(value, str) and value.lower() in month_mapping:
                            month_num = month_mapping[value.lower()]
                            query += f"strftime('%m', e.date) {op_type} ?"
                            params.append(month_num)
                        else:
                            # Assume it's a number
                            query += f"strftime('%m', e.date) {op_type} ?"
                            # Ensure month is zero-padded
                            if isinstance(value, str) and len(value) == 1:
                                params.append(value.zfill(2))
                            else:
                                params.append(value)
                    query += ")"
                    continue
                
                # Additional validation for date field
                if field == "date":
                    connector = "WHERE" if "WHERE" not in query else "AND"
                    query += f" {connector} ("
                    first = True
                    for constraint in filters[field]:
                        op_type, value = constraint
                        # Validate date format
                        if not self._validate_date(value):
                            print(f"Error: Invalid date format '{value}' in filter. Must be in YYYY-MM-DD format.")
                            return False
                        
                        if not first:
                            query += f" {op} "
                        first = False
                        query += f"e.date {op_type} ?"
                        params.append(value)
                    query += ")"
                    continue
                    
                # Handle regular fields with mapping to actual DB columns
                field_mapping = {
                    "amount": "e.amount",
                    "date": "e.date",
                    "category": "c.category_name",
                    "tag": "t.tag_name",
                    "payment_method": "pm.payment_method_name"
                }
                
                db_field = field_mapping.get(field, field)
                connector = "WHERE" if "WHERE" not in query else "AND"
                query += f" {connector} ("
                first = True
                for constraint in filters[field]:
                    op_type, value = constraint
                    if not first:
                        query += f" {op} "
                    first = False
                    query += f"{db_field} {op_type} ?"
                    params.append(value)
                query += ")"
            
            # Execute the query and display results
            self.cursor.execute(query, params)
            expenses = self.cursor.fetchall()
            
            if not expenses:
                print("No expenses found matching the criteria.")
                return True
            
            # Display results in a formatted table
            print("\nExpense List:")
            print("-" * 95)
            
            # Add username column for admin view
            if user_role == "admin":
                print(f"{'ID':<5} {'Date':<12} {'Amount':<10} {'Category':<15} {'Tag':<15} {'Payment Method':<15} {'Username':<10} {'Description':<25}")
                print("-" * 95)
                
                for expense in expenses:
                    expense_id, date, amount, description, category, tag, payment_method, username = expense
                    # Handle NULL values from LEFT JOINs
                    category = category or "N/A"
                    tag = tag or "N/A"
                    payment_method = payment_method or "N/A"
                    username = username or "N/A"
                    description = (description[:22] + "...") if description and len(description) > 25 else (description or "")
                    print(f"{expense_id:<5} {date:<12} {amount:<10.2f} {category:<15} {tag:<15} {payment_method:<15} {username:<10} {description:<25}")
            else:
                # Original display for regular users
                print(f"{'ID':<5} {'Date':<12} {'Amount':<10} {'Category':<15} {'Tag':<15} {'Payment Method':<15} {'Description':<30}")
                print("-" * 95)
                
                for expense in expenses:
                    expense_id, date, amount, description, category, tag, payment_method, _ = expense
                    # Handle NULL values from LEFT JOINs
                    category = category or "N/A"
                    tag = tag or "N/A"
                    payment_method = payment_method or "N/A"
                    description = (description[:27] + "...") if description and len(description) > 30 else (description or "")
                    
                    print(f"{expense_id:<5} {date:<12} {amount:<10.2f} {category:<15} {tag:<15} {payment_method:<15} {description:<30}")
            
            print("-" * 95)
            print(f"Total: {len(expenses)} expense(s) found")
            return True
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return False
        except Exception as e:
            print(f"Error listing expenses: {e}")
            return False