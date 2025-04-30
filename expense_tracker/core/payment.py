import sqlite3
from expense_tracker.database.sql_queries import PAYMENT_QUERIES

class PaymentManager:
    def __init__(self, cursor, conn):
        self.conn = conn
        self.cursor = cursor
    
    def add_payment_method(self, payment_method_name):
        payment_method_name = payment_method_name.strip().lower()
        
        if not payment_method_name:
            print("Error : Payment Method cannot be empty.")
            return False
        
        try:
            self.cursor.execute(PAYMENT_QUERIES["add_payment_method"], (payment_method_name,))
            self.conn.commit()
            print(f"Payment method '{payment_method_name}' added successfully.")
            return True
        except sqlite3.IntegrityError:
            print(f"Error: Payment method '{payment_method_name}' already exists.")
            return False
    
    def list_payment_methods(self):
        self.cursor.execute(PAYMENT_QUERIES["list_payment_methods"])
        methods = self.cursor.fetchall()

        if not methods:
            print("No payment methods found.")
        else:
            print("Payment Methods:")
            print("-" * 20)
            for method in methods:
                print(f"- {method[0]}")
        return True

    def delete_payment_method(self, payment_method_name):
        """Deletes a payment method and all related data."""
        try:
            # Check if payment method exists
            self.cursor.execute("SELECT payment_method_id FROM Payment_Method WHERE payment_method_name = ?", (payment_method_name,))
            if not self.cursor.fetchone():
                print(f"Error: Payment method '{payment_method_name}' does not exist.")
                return False

            # Delete related entries
            self.cursor.execute(PAYMENT_QUERIES["delete_payment_related"], (payment_method_name,))
            # Delete the payment method
            self.cursor.execute(PAYMENT_QUERIES["delete_payment_method"], (payment_method_name,))
            self.conn.commit()
            print(f"Payment method '{payment_method_name}' and related data deleted successfully.")
            return True
        except sqlite3.Error as e:
            print(f"Error: Unable to delete payment method '{payment_method_name}'. {e}")
            return False