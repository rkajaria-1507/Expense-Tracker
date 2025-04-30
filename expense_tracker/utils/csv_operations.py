import csv
import sqlite3
from expense_tracker.database.sql_queries import CSV_QUERIES

class CSVOperations:
    def __init__(self, cursor, conn, expense_manager=None):
        self.conn = conn
        self.cursor = cursor
        self.expense_manager = expense_manager
        self.current_user = None
    
    def set_current_user(self, username):
        self.current_user = username
        if self.expense_manager:
            self.expense_manager.set_current_user(username)
    
    def import_expenses(self, file_path):
        if not self.current_user:
            print("Error: No user logged in")
            return False
            
        try:
            success_count = 0
            error_count = 0
            duplicate_count = 0  # Track duplicates
            
            with open(file_path, "r") as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Validate CSV header
                required_fields = ["amount", "category", "payment_method", "date", "description", "tag"]
                for field in required_fields:
                    if field not in reader.fieldnames:
                        print("Error: CSV header does not match")
                        return False
                
                for row in reader:
                    amount = row.get('amount', '')
                    category = row.get('category', '').lower()
                    payment_method = row.get('payment_method', '').lower()
                    date = row.get('date', '')
                    description = row.get('description', '')
                    tag = row.get('tag', '')
                    payment_detail = row.get('payment_detail_identifier', '')
                    
                    # Attempt to add each expense
                    result = self.expense_manager.addexpense(
                        amount=amount,
                        category=category,
                        payment_method=payment_method,
                        date=date,
                        description=description,
                        tag=tag,
                        payment_detail_identifier=payment_detail,
                        import_fn=1  # Flag to suppress individual success messages
                    )
                    
                    if result == "duplicate":
                        duplicate_count += 1
                    elif result:
                        success_count += 1
                    else:
                        error_count += 1
            
            print(f"Import completed: {success_count} expenses added successfully, {duplicate_count} duplicates skipped, {error_count} errors.")
            return True
                
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found")
            return False
        except Exception as e:
            print(f"Error importing expenses: {e}")
            return False
    
    def export_csv(self, file_path, sort_field=None):
        # Mapping allowed sort fields to actual SQL columns
        sort_fields = {
            "amount": "e.amount",
            "category": "c.category_name",
            "payment_method": "pm.payment_method_name",
            "date": "e.date",
            "description": "e.description",
            "tag": "t.tag_name",
            "payment_detail_identifier": "pme.payment_detail_identifier"
        }
        
        query = CSV_QUERIES["export_base"]
        
        # Add sorting only if sort_field is provided and valid
        if sort_field:
            if sort_field not in sort_fields:
                print("Error: Invalid sort field.")
                return False
            query += f" ORDER BY {sort_fields[sort_field]}"

        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        if not rows:
            print("No expenses found to export.")
            return False

        try:
            with open(file_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                # Write header row
                writer.writerow(['amount', 'category', 'payment_method', 'date', 'description', 'tag', 'payment_detail_identifier'])
                # Write data rows
                writer.writerows(rows)
            
            print(f"Expenses exported successfully to {file_path}")
            return True
        except Exception as e:
            print(f"Error exporting expenses: {e}")
            return False