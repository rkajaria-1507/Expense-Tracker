import sqlite3
from datetime import datetime
from sql_queries import LOG_QUERIES

class LogManager:
    def __init__(self, cursor, conn):
        self.conn = conn
        self.cursor = cursor
        self.current_user = None
    
    def set_current_user(self, username):
        """Set the current user for logging purposes"""
        self.current_user = username
    
    def add_log(self, description):
        """Add a log entry for the current user"""
        if not self.current_user:
            return False
            
        try:
            self.cursor.execute(LOG_QUERIES["add_log"], (self.current_user, description))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding log entry: {e}")
            return False
    
    def get_user_logs(self, username=None, limit=50):
        """Get logs for a specific user or all users if admin"""
        try:
            if username:
                self.cursor.execute(LOG_QUERIES["get_user_logs"], (username, limit))
            else:
                self.cursor.execute(LOG_QUERIES["get_all_logs"], (limit,))
            
            logs = self.cursor.fetchall()
            return logs
        except sqlite3.Error as e:
            print(f"Error retrieving logs: {e}")
            return []
    
    def display_logs(self, username=None, limit=50):
        """Display logs for a specific user or all users if admin"""
        logs = self.get_user_logs(username, limit)
        
        if not logs:
            if username:
                print(f"No logs found for user '{username}'")
            else:
                print("No logs found")
            return
        
        print("\nLog Entries:")
        print("-" * 100)
        print(f"{'ID':<5} {'Timestamp':<20} {'Username':<15} {'Description':<60}")
        print("-" * 100)
        
        for log in logs:
            logid, timestamp, user, description = log
            # Format the timestamp for better readability
            formatted_time = timestamp
            print(f"{logid:<5} {formatted_time:<20} {user:<15} {description:<60}")
        
        print("-" * 100)
    
    def generate_log_description(self, action_type, params=None):
        """Generate a standardized log description based on action type and parameters"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if action_type == "login":
            return f"[{timestamp}] User logged in"
        elif action_type == "logout":
            return f"[{timestamp}] User logged out"
        elif action_type == "register":
            username = params[0] if params else "unknown"
            role = params[1] if len(params) > 1 else "unknown"
            return f"[{timestamp}] Added new user '{username}' with role '{role}'"
        elif action_type == "add_category":
            category = params[0] if params else "unknown"
            return f"[{timestamp}] Added new category '{category}'"
        elif action_type == "add_payment_method":
            payment_method = params[0] if params else "unknown"
            return f"[{timestamp}] Added new payment method '{payment_method}'"
        elif action_type == "add_expense":
            return f"[{timestamp}] Added new expense"
        elif action_type == "update_expense":
            expense_id = params[0] if params else "unknown"
            field = params[1] if len(params) > 1 else "unknown"
            return f"[{timestamp}] Updated expense ID '{expense_id}', field '{field}'"
        elif action_type == "delete_expense":
            expense_id = params[0] if params else "unknown"
            return f"[{timestamp}] Deleted expense ID '{expense_id}'"
        elif action_type == "import_expenses":
            file_path = params[0] if params else "unknown"
            return f"[{timestamp}] Imported expenses from '{file_path}'"
        elif action_type == "export_expenses":
            file_path = params[0] if params else "unknown"
            return f"[{timestamp}] Exported expenses to '{file_path}'"
        elif action_type == "report":
            report_type = params[0] if params else "unknown"
            if report_type == "top_expenses":
                n = params[1] if len(params) > 1 else "unknown"
                start_date = params[2] if len(params) > 2 else "unknown"
                end_date = params[3] if len(params) > 3 else "unknown"
                return f"[{timestamp}] Generated top {n} expenses report ({start_date} to {end_date})"
            else:
                param_str = ", ".join(params[1:]) if len(params) > 1 else ""
                if param_str:
                    return f"[{timestamp}] Generated {report_type} report with params: {param_str}"
                else:
                    return f"[{timestamp}] Generated {report_type} report"
        elif action_type == "view_logs":
            limit = params[0] if params else "50"
            return f"[{timestamp}] Viewed system logs (limit: {limit})"
        else:
            return f"[{timestamp}] {action_type}"