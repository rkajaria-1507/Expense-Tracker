import sqlite3
from expense_tracker.database.sql_queries import USER_QUERIES

class UserManager:
    def __init__(self, cursor, conn):
        self.conn = conn
        self.cursor = cursor
        self.current_user = None
        self.privileges = None
    
    def authenticate(self, username, password):
        self.cursor.execute(USER_QUERIES["get_user"], (username,))
        user = self.cursor.fetchone()
        
        if user and user[1] == password:
            self.current_user = username
            
            # Get user role
            self.cursor.execute(USER_QUERIES["get_user_role"], (username,))
            role = self.cursor.fetchone()
            if role:
                self.privileges = role[0]
            
            print(f"Welcome, {username}! You are logged in as {self.privileges}.")
            return True
        else:
            if user is None:
                print("Error: Username does not exist.")
            else:
                print("Error: Incorrect password.")
            return False
    
    def logout(self):
        if self.current_user:
            print(f"Logging Out: Goodbye, {self.current_user}!")
            self.current_user = None
            self.privileges = None
            return True
        else:
            print("Error: No user is currently logged in.")
            return False
    
    def register(self, username, password, role='user'):
        # Validate inputs
        if not username or not password:
            return False, "Username and password cannot be empty."
        # Get role_id for given role
        # Only admins may create users with roles other than 'user'
        if role != 'user':
            if self.current_user is None or self.privileges != 'admin':
                return False, "Only admins can assign non-user roles."

        self.cursor.execute(USER_QUERIES["get_role_id"], (role,))
        result = self.cursor.fetchone()
        if result is None:
            return False, f"Role '{role}' does not exist."
        
        role_id = result[0]  # Extract role_id

        try:
            self.cursor.execute(USER_QUERIES["insert_user"], (username, password))
            self.cursor.execute(USER_QUERIES["insert_user_role"], (username, role_id))
            self.conn.commit()
            return True, ""
        except sqlite3.IntegrityError:
            return False, f"Username '{username}' already exists."
    
    def list_users(self):
        self.cursor.execute(USER_QUERIES["list_users"])
        users = self.cursor.fetchall()
        
        if not users:
            print("No users found!!")
        else:
            print("\nUser List:")
            print("-" * 35)
            print(f"{'Username':<20} {'Role':<15}")
            print("-" * 35)
            for user in users:
                username, role = user
                print(f"{username:<20} {role:<15}")
            print("-" * 35)
        return True
    
    def help(self, current_privileges, list_of_privileges):
        if self.current_user is None:
            print("Available commands:")
            print("- login <username> <password>")
            print("- help")
            print("- exit")
        else:
            print("Available commands:")
            # Display regular commands
            for command, syntax in list_of_privileges[current_privileges].items():
                if command != "report":  # Handle report separately
                    print(f"- {syntax}")
            
            # Display report commands if available
            if "report" in list_of_privileges[current_privileges]:
                print("\nReport commands:")
                for _, syntax in list_of_privileges[current_privileges]["report"].items():
                    print(f"- {syntax}")
                    
            print("\nOther commands:")
            print("- logout")
            print("- help")
            print("- exit")
        return True
    
    def delete_user(self, username):
        """Deletes a user and all related data."""
        try:
            # Check if user exists
            self.cursor.execute("SELECT username FROM User WHERE username = ?", (username,))
            if not self.cursor.fetchone():
                print(f"Error: User '{username}' does not exist.")
                return False

            # Fetch all expenses of this user
            self.cursor.execute("SELECT expense_id FROM User_Expense WHERE username = ?", (username,))
            expense_ids = [row[0] for row in self.cursor.fetchall()]
            # Delete related expense data
            for eid in expense_ids:
                self.cursor.execute("DELETE FROM Category_Expense WHERE expense_id = ?", (eid,))
                self.cursor.execute("DELETE FROM Tag_Expense WHERE expense_id = ?", (eid,))
                self.cursor.execute("DELETE FROM Payment_Method_Expense WHERE expense_id = ?", (eid,))
                self.cursor.execute("DELETE FROM User_Expense WHERE expense_id = ?", (eid,))
                self.cursor.execute("DELETE FROM Expense WHERE expense_id = ?", (eid,))

            # Delete user logs
            self.cursor.execute(USER_QUERIES["delete_user_related"], (username,))
            # Delete user roles
            self.cursor.execute(USER_QUERIES["delete_user_role"], (username,))
            # Delete the user
            self.cursor.execute(USER_QUERIES["delete_user"], (username,))

            self.conn.commit()
            print(f"User '{username}' and all related data have been deleted successfully.")
            
            # If user deleted themselves, log them out
            if self.current_user == username:
                print("You have deleted your own account. Logging out...")
                self.current_user = None
                self.privileges = None
            return True
        except sqlite3.Error as e:
            print(f"Error: Unable to delete user '{username}'. {e}")
            return False