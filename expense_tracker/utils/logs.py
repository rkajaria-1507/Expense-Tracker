import sqlite3
from datetime import datetime
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from expense_tracker.database.sql_queries import LOG_QUERIES

class LogManager:
    def __init__(self, cursor, conn):
        self.conn = conn
        self.cursor = cursor
        self.current_user = None
    
    def set_current_user(self, username):
        self.current_user = username
    
    def add_log(self, description):
        if not self.current_user:
            return False
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute(
                LOG_QUERIES["add_log_with_description"],
                (self.current_user, timestamp, description)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding log: {e}")
            return False
    
    def generate_log_description(self, action_type, parameters=None):
        description = ""

        if action_type == "login":
            description = "User logged in successfully"
        elif action_type == "logout":
            description = "User logged out"
        elif action_type == "add_expense":
            description = "Added a new expense"
        elif action_type == "update_expense":
            description = f"Updated expense ID {parameters[0]} - field: {parameters[1]}"
        elif action_type == "delete_expense":
            description = f"Deleted expense ID {parameters[0]}"
        elif action_type == "add_category":
            description = f"Added new category: {parameters[0]}"
        elif action_type == "delete_category":
            description = f"Deleted category: {parameters[0]}"
        elif action_type == "add_payment_method":
            description = f"Added new payment method: {parameters[0]}"
        elif action_type == "register":
            description = f"Created new user: {parameters[0]} with role: {parameters[1]}"
        elif action_type == "delete_user":
            description = f"Deleted user: {parameters[0]}"
        elif action_type == "import_expenses":
            description = f"Imported {parameters[0]} expenses from CSV"
        elif action_type == "export_expenses":
            description = "Exported expenses to CSV"
        else:
            description = f"Performed action: {action_type}"

        return description
    
    def view_logs(self, filters=None):
        try:
            query = LOG_QUERIES["view_logs_base"]
            params = []

            if filters:
                if 'username' in filters:
                    query += " WHERE username = ?"
                    params.append(filters['username'])

                if 'start_date' in filters:
                    if 'username' in filters:
                        query += " AND DATE(timestamp) >= DATE(?)"
                    else:
                        query += " WHERE DATE(timestamp) >= DATE(?)"
                    params.append(filters['start_date'])

                if 'end_date' in filters:
                    if 'username' in filters or 'start_date' in filters:
                        query += " AND DATE(timestamp) <= DATE(?)"
                    else:
                        query += " WHERE DATE(timestamp) <= DATE(?)"
                    params.append(filters['end_date'])

            query += LOG_QUERIES["view_logs_order"]
            self.cursor.execute(query, tuple(params))
            logs = self.cursor.fetchall()

            if not logs:
                print("No logs found.")
            else:
                print("\nActivity Logs:")
                print("-" * 100)
                print(f"{'ID':<5} {'Username':<15} {'Timestamp':<20} {'Description':<60}")
                print("-" * 100)

                for log in logs:
                    logid, username, timestamp, description = log
                    if len(description) > 60:
                        description = description[:57] + "..."
                    print(f"{logid:<5} {username:<15} {timestamp:<20} {description:<60}")

                print("-" * 100)
                print(f"Total: {len(logs)} log(s) found.")

            return True
        except sqlite3.Error as e:
            print(f"Error viewing logs: {e}")
            return False

    def get_users_with_logs(self):
        try:
            self.cursor.execute(LOG_QUERIES["get_users_with_logs"])
            users = self.cursor.fetchall()
            return [u[0] for u in users]
        except sqlite3.Error as e:
            print(f"Error getting users with logs: {e}")
            return []
