import shlex
from constants import list_of_privileges

class CommandParser:
    def __init__(self, user_manager, category_manager, payment_manager, expense_manager, csv_operations, report_manager, log_manager):
        self.user_manager = user_manager
        self.category_manager = category_manager
        self.payment_manager = payment_manager
        self.expense_manager = expense_manager
        self.csv_operations = csv_operations
        self.report_manager = report_manager
        self.log_manager = log_manager
    
    def parse(self, cmd_str):
        cmd_str = cmd_str.strip()
        try:
            cmd_str_lst = shlex.split(cmd_str)  # Use shlex.split for parsing
        except ValueError as e:
            print("\n" + "─" * 50)
            print(f"❌ Error: {e}")  # Handle quote-closing errors
            print("─" * 50 + "\n")
            return
        
        if not cmd_str_lst:
            print("\n" + "─" * 50)
            print("❌ Error: No command entered.")
            print("─" * 50 + "\n")
            return
        
        cmd = cmd_str_lst[0]
        
        # Handling help -  available for all users
        if cmd == "help":
            if len(cmd_str_lst) != 1:
                print("\n" + "─" * 50)
                print("❌ Error: No arguments required")
                print("─" * 50 + "\n")
            else:
                # Add spacing before help output
                print()
                self.user_manager.help(self.user_manager.privileges or "user", list_of_privileges)
                # Add spacing after help output
                print()
                if self.user_manager.current_user:
                    self.log_manager.add_log(self.log_manager.generate_log_description("help"))
            return
        
        # Handling login
        elif cmd == "login":
            if len(cmd_str_lst) != 3:
                print("\n" + "─" * 50)
                print("❌ Error: Insufficient number of arguments")
                print("─" * 50 + "\n")
                return
            if self.user_manager.current_user is None:
                username = cmd_str_lst[1]
                password = cmd_str_lst[2]
                if self.user_manager.authenticate(username, password):
                    # Update user info in other managers
                    self.expense_manager.set_current_user(username)
                    self.csv_operations.set_current_user(username)
                    self.report_manager.set_user_info(username, self.user_manager.privileges)
                    self.log_manager.set_current_user(username)  # Add this line
                    self.log_manager.add_log(self.log_manager.generate_log_description("login"))
            else:
                print("\n" + "─" * 50)
                print("❌ Error: Another session is live!")
                print("─" * 50 + "\n")
            return

        # Handling logout
        elif cmd == "logout":
            if len(cmd_str_lst) != 1:
                print("\n" + "─" * 50)
                print("❌ Error: Insufficient number of arguments")
                print("─" * 50 + "\n")
                return
            if self.user_manager.current_user is not None:
                self.log_manager.add_log(self.log_manager.generate_log_description("logout"))
                self.user_manager.logout()
                # Clear user info in other managers
                self.expense_manager.set_current_user(None)
                self.csv_operations.set_current_user(None)
                self.report_manager.set_user_info(None, None)
                self.log_manager.set_current_user(None)  # Add this line
            else:
                print("\n" + "─" * 50)
                print("❌ Error: User not logged in!")
                print("─" * 50 + "\n")
            return

        # Ensure user is logged in for further commands
        if self.user_manager.current_user is None:
            print("\n" + "─" * 50)
            print("❌ Error: Please login!")
            print("─" * 50 + "\n")
            return

        # Ensure the command exists in privileges
        if cmd not in list_of_privileges['admin'] and cmd not in list_of_privileges["user"]:
            print("\n" + "─" * 50)
            print("❌ Error: Invalid command")
            print("─" * 50 + "\n")
            return

        # Ensure the user has permission
        if cmd not in list_of_privileges[self.user_manager.privileges]:
            print("\n" + "─" * 50)
            print("❌ Error: Unauthorized command")
            print("─" * 50 + "\n")
            return

        # Handling add_user (Admin only)
        if cmd == "add_user":
            if len(cmd_str_lst) == 4:
                username = cmd_str_lst[1]
                password = cmd_str_lst[2]
                role = cmd_str_lst[3]
                if self.user_manager.register(username, password, role):
                    self.log_manager.add_log(self.log_manager.generate_log_description("add_user", [username, "", role]))
                    print("\n" + "─" * 50)
                    print(f"✓ User '{username}' successfully added with role '{role}'")
                    print("─" * 50 + "\n")
            else:
                print("\n" + "─" * 50)
                print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges['admin']['add_user']}")
                print("─" * 50 + "\n")

        # Handling list_categories
        elif cmd == "list_categories":
            if len(cmd_str_lst) != 1:
                print("\n" + "─" * 50)
                print("❌ Error: No arguments required")
                print("─" * 50 + "\n")
            else:
                # Add spacing before displaying list
                print()
                self.category_manager.list_categories()
                # Add spacing after displaying list
                print()
                self.log_manager.add_log(self.log_manager.generate_log_description("list_categories"))

        # Handling add_category (Admin only)
        elif cmd == "add_category":
            if len(cmd_str_lst) != 2:
                print("\n" + "─" * 50)
                print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges['admin']['add_category']}")
                print("─" * 50 + "\n")
            else:
                category_name = cmd_str_lst[1]
                if self.category_manager.add_category(category_name):
                    print("\n" + "─" * 50)
                    print(f"✓ Category '{category_name}' successfully added")
                    print("─" * 50 + "\n")
                    self.log_manager.add_log(self.log_manager.generate_log_description("add_category", [category_name]))

        # Handling list_payment_methods
        elif cmd == "list_payment_methods":
            if len(cmd_str_lst) != 1:
                print("\n" + "─" * 50)
                print("❌ Error: No arguments required")
                print("─" * 50 + "\n")
            else:
                # Add spacing before displaying list
                print()
                self.payment_manager.list_payment_methods()
                # Add spacing after displaying list
                print()
                self.log_manager.add_log(self.log_manager.generate_log_description("list_payment_methods"))

        # Handling add_payment_method (Admin only)
        elif cmd == "add_payment_method":
            if len(cmd_str_lst) != 2:
                print("\n" + "─" * 50)
                print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges['admin']['add_payment_method']}")
                print("─" * 50 + "\n")
            else:
                payment_method_name = cmd_str_lst[1]
                if self.payment_manager.add_payment_method(payment_method_name):
                    print("\n" + "─" * 50)
                    print(f"✓ Payment method '{payment_method_name}' successfully added")
                    print("─" * 50 + "\n")
                    self.log_manager.add_log(self.log_manager.generate_log_description("add_payment_method", [payment_method_name]))

        # Handling addexpense
        elif cmd == "add_expense":
            if len(cmd_str_lst) == 6 or len(cmd_str_lst) == 7:  #  description is optional. Therefore 6 arguments are also fine
                amount = cmd_str_lst[1]
                category_name = cmd_str_lst[2]
                payment_method_name = cmd_str_lst[3]
                date_txt = cmd_str_lst[4]
                tag_name = cmd_str_lst[-1]
                
                # Handle optional description
                if len(cmd_str_lst) == 6:  # No description provided
                    description = ""
                else:  # Description is provided
                    description = cmd_str_lst[5]
                    
                payment_detail_identifier = ""
                choice = input("Would you like to add payment method details?(y/n) [Type more to display more info]: ")
                if choice.lower() == "more":
                    print("This detail can be used by the used by the user to generate reports based on specific payment method")
                    print("The details will be masked")
                    choice = input("Would you like to add payment method details?(y/n): ")
                if choice.lower() == "y":
                    payment_detail_identifier = input("Enter the details: ")
                if self.expense_manager.addexpense(amount, category_name, payment_method_name, date_txt, description, tag_name, payment_detail_identifier):
                    print("\n" + "─" * 50)
                    print(f"✓ Expense of amount '{amount}' successfully added")
                    print("─" * 50 + "\n")
                    self.log_manager.add_log(self.log_manager.generate_log_description("add_expense", [amount, category_name, payment_method_name]))
                
            else:
                print("\n" + "─" * 50)
                print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges['user']['add_expense']}")
                print("─" * 50 + "\n")
                return

        # Handling update_expense
        elif cmd == "update_expense":
            if len(cmd_str_lst) == 4:
                expense_id = cmd_str_lst[1]
                field = cmd_str_lst[2]
                new_value = cmd_str_lst[3]
                if self.expense_manager.update_expense(expense_id, field, new_value):
                    print("\n" + "─" * 50)
                    print(f"✓ Expense '{expense_id}' successfully updated")
                    print("─" * 50 + "\n")
                    self.log_manager.add_log(self.log_manager.generate_log_description("update_expense", [expense_id, field, new_value]))
            else:
                print("\n" + "─" * 50)
                print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges['user']['update_expense']}")
                print("─" * 50 + "\n")

        # Handling delete_expense
        elif cmd == "delete_expense":
            if len(cmd_str_lst) == 2:
                expense_id = cmd_str_lst[1]
                if self.expense_manager.delete_expense(expense_id):
                    print("\n" + "─" * 50)
                    print(f"✓ Expense '{expense_id}' successfully deleted")
                    print("─" * 50 + "\n")
                    self.log_manager.add_log(self.log_manager.generate_log_description("delete_expense", [expense_id]))
            else:
                print("\n" + "─" * 50)
                print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges['user']['delete_expense']}")
                print("─" * 50 + "\n")
        
        elif cmd == "list_expenses":
            field_dict = {
                "amount": [],
                "date": [],
                "category": [],
                "tag": [],
                "payment_method": [],
                "month": []
            }
            
            field_op = ["<=",">=","=","<",">"]
            if len(cmd_str_lst) > 1:
                # Extract the part after the command
                filter_part = cmd_str[len(cmd):].strip()
                # Split by comma to get individual constraints
                constraint_list = filter_part.split(',')
                
                for constraint in constraint_list:
                    constraint = constraint.strip()
                    operator_found = False
                    
                    # Try each operator to see if it exists in the constraint
                    for op in field_op:
                        if op in constraint:
                            # Split by operator
                            parts = constraint.split(op, 1)  # Split only on first occurrence
                            if len(parts) == 2:
                                field = parts[0].strip()
                                value = parts[1].strip()
                                
                                # Validate field
                                if field not in field_dict:
                                    print("\n" + "─" * 50)
                                    print(f"❌ Error: Invalid field '{field}'")
                                    print("─" * 50 + "\n")
                                    return
                                
                                # Add to field_dict
                                field_dict[field].append([op, value])
                                operator_found = True
                                break
                            else:
                                print("\n" + "─" * 50)
                                print("❌ Error : Invalid Filter !!")
                                print("─" * 50 + "\n")
                    
                    if not operator_found:
                        print("\n" + "─" * 50)
                        print(f"❌ Error: No valid operator found in filter '{constraint}'")
                        print("─" * 50 + "\n")
                        return
                
                # Add header before calling list_expenses
                print("\n" + "═" * 80)
                print("📋 EXPENSES LIST".center(80))
                print(f"Filter: {filter_part}".center(80))
                print("═" * 80)
                
                self.expense_manager.list_expenses(field_dict, self.user_manager.privileges)
                self.log_manager.add_log(self.log_manager.generate_log_description("list_expenses", [filter_part]))
            else:
                # Add header before calling list_expenses
                print("\n" + "═" * 80)
                print("📋 EXPENSES LIST".center(80))
                print("═" * 80)
                
                self.expense_manager.list_expenses(user_role=self.user_manager.privileges)
                self.log_manager.add_log(self.log_manager.generate_log_description("list_expenses"))
                    
        elif cmd == "import_expenses":
            if len(cmd_str_lst) != 2:
                print("\n" + "─" * 50)
                print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges['user']['import_expenses']}")
                print("─" * 50 + "\n")
            else:
                file_path = cmd_str_lst[1]
                result = self.csv_operations.import_expenses(file_path)
                print("\n" + "─" * 50)
                print(f"✓ Expenses successfully imported from '{file_path}'")
                print("─" * 50 + "\n")
                self.log_manager.add_log(self.log_manager.generate_log_description("import_expenses", [file_path], {"success": result}))

        elif cmd == "export_csv":
            # Split by comma to check for optional sort-on parameter
            parts = cmd_str.strip().split(',', 1)
            export_cmd = parts[0].strip()
            
            # Get file path based on whether it's quoted or not
            if '"' in export_cmd or "'" in export_cmd:
                # If quoted, use shlex for proper quote handling
                cmd_parts = shlex.split(export_cmd)
                if len(cmd_parts) < 2:
                    print("\n" + "─" * 50)
                    print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges['user']['export_csv']}")
                    print("─" * 50 + "\n")
                    return
                file_path = cmd_parts[1]
            else:
                # If not quoted, use string slicing approach
                if export_cmd.startswith("export_csv "):
                    file_path = export_cmd[len("export_csv "):].strip()
                else:
                    print("\n" + "─" * 50)
                    print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges['user']['export_csv']}")
                    print("─" * 50 + "\n")
                    return
            
            if not file_path:
                print("\n" + "─" * 50)
                print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges['user']['export_csv']}")
                print("─" * 50 + "\n")
                return
            
            # Check for optional sort-on parameter
            if len(parts) > 1:
                sort_part = parts[1].strip()
                sort_parts = shlex.split(sort_part)
                
                if len(sort_parts) != 2 or sort_parts[0].lower() != "sort-on":
                    print("\n" + "─" * 50)
                    print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges['user']['export_csv']}")
                    print("─" * 50 + "\n")
                    return
                    
                sort_field = sort_parts[1].lower()
                if self.csv_operations.export_csv(file_path, sort_field):
                    print("\n" + "─" * 50)
                    print(f"✓ CSV successfully exported to '{file_path}' sorted by '{sort_field}'")
                    print("─" * 50 + "\n")
                    self.log_manager.add_log(self.log_manager.generate_log_description("export_csv", [file_path, sort_field]))
            else:
                # No sorting specified
                if self.csv_operations.export_csv(file_path):
                    print("\n" + "─" * 50)
                    print(f"✓ CSV successfully exported to '{file_path}'")
                    print("─" * 50 + "\n")
                    self.log_manager.add_log(self.log_manager.generate_log_description("export_csv", [file_path]))
                
        # Handling list_users (Admin only)
        elif cmd == "list_users":
            if len(cmd_str_lst) != 1:
                print("\n" + "─" * 50)
                print("❌ Error: No arguments required")
                print("─" * 50 + "\n")
            else:
                # Add spacing before displaying list
                print()
                self.user_manager.list_users()
                # Add spacing after displaying list
                print()
                self.log_manager.add_log(self.log_manager.generate_log_description("list_users"))

        # Handling delete_user command
        elif cmd == "delete_user":
            if self.user_manager.privileges == "admin":
                if len(cmd_str_lst) != 2:
                    print("\n" + "\u2500" * 50)
                    print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges['admin']['delete_user']}")
                    print("\u2500" * 50 + "\n")
                else:
                    username = cmd_str_lst[1]
                    if self.user_manager.delete_user(username):
                        self.log_manager.add_log(self.log_manager.generate_log_description("delete_user", [username]))
            elif self.user_manager.privileges == "user":
                if len(cmd_str_lst) != 1:
                    print("\n" + "\u2500" * 50)
                    print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges['user']['delete_user']}")
                    print("\u2500" * 50 + "\n")
                else:
                    if self.user_manager.delete_user(self.user_manager.current_user):
                        self.log_manager.add_log(self.log_manager.generate_log_description("delete_user", [self.user_manager.current_user]))

        # Handling delete_category command
        elif cmd == "delete_category":
            if len(cmd_str_lst) != 2:
                print("\n" + "\u2500" * 50)
                print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges['admin']['delete_category']}")
                print("\u2500" * 50 + "\n")
            else:
                category_name = cmd_str_lst[1]
                if self.category_manager.delete_category(category_name):
                    self.log_manager.add_log(self.log_manager.generate_log_description("delete_category", [category_name]))

        # Handling report commands
        elif cmd == "report":
            if len(cmd_str_lst) < 2:
                print("\n" + "─" * 50)
                print("❌ Error: Report type not specified")
                print("Available report types for your role:")
                for report_type, syntax in list_of_privileges[self.user_manager.privileges]["report"].items():
                    print(f"- {syntax}")
                print("─" * 50 + "\n")
                return
                
            report_type = cmd_str_lst[1]
            
            # Add a report header before execution
            print("\n" + "═" * 80)
            print(f"📊 GENERATING REPORT: {report_type.upper().replace('_', ' ')}".center(80))
            print("═" * 80)
            
            # Check if the report type is valid for the user's role
            if report_type not in list_of_privileges[self.user_manager.privileges]["report"]:
                print("\n" + "─" * 50)
                print(f"❌ Error: Invalid or unauthorized report type '{report_type}'")
                print("─" * 50 + "\n")
                return
            
            # Handle different report types
            if report_type == "top_expenses":
                if len(cmd_str_lst) != 5:
                    print("\n" + "─" * 50)
                    print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges[self.user_manager.privileges]['report']['top_expenses']}")
                    print("─" * 50 + "\n")
                else:
                    n = cmd_str_lst[2]
                    start_date = cmd_str_lst[3]
                    end_date = cmd_str_lst[4]
                    self.report_manager.generate_report_top_expenses(n, start_date, end_date)
                    self.log_manager.add_log(self.log_manager.generate_log_description("report", ["top_expenses", n, start_date, end_date]))
                    
            elif report_type == "category_spending":
                if len(cmd_str_lst) != 3:
                    print("\n" + "─" * 50)
                    print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges[self.user_manager.privileges]['report']['category_spending']}")
                    print("─" * 50 + "\n")
                else:
                    category = cmd_str_lst[2]
                    self.report_manager.generate_report_category_spending(category)
                    self.log_manager.add_log(self.log_manager.generate_log_description("report", ["category_spending", category]))
                    
            elif report_type == "above_average_expenses":
                if len(cmd_str_lst) != 2:
                    print("\n" + "─" * 50)
                    print("❌ Error: No additional arguments required")
                    print("─" * 50 + "\n")
                else:
                    self.report_manager.generate_report_above_average_expenses()
                    self.log_manager.add_log(self.log_manager.generate_log_description("report", ["above_average_expenses"]))
                    
            elif report_type == "monthly_category_spending":
                if len(cmd_str_lst) != 2:
                    print("\n" + "─" * 50)
                    print("❌ Error: No additional arguments required")
                    print("─" * 50 + "\n")
                else:
                    self.report_manager.generate_report_monthly_category_spending()
                    self.log_manager.add_log(self.log_manager.generate_log_description("report", ["monthly_category_spending"]))
                    
            elif report_type == "highest_spender_per_month":
                if len(cmd_str_lst) != 2:
                    print("\n" + "─" * 50)
                    print("❌ Error: No additional arguments required")
                    print("─" * 50 + "\n")
                else:
                    self.report_manager.generate_report_highest_spender_per_month()
                    self.log_manager.add_log(self.log_manager.generate_log_description("report", ["highest_spender_per_month"]))
                    
            elif report_type == "frequent_category":
                if len(cmd_str_lst) != 2:
                    print("\n" + "─" * 50)
                    print("❌ Error: No additional arguments required")
                    print("─" * 50 + "\n")
                else:
                    self.report_manager.generate_report_frequent_category()
                    self.log_manager.add_log(self.log_manager.generate_log_description("report", ["frequent_category"]))
                    
            elif report_type == "payment_method_usage":
                if len(cmd_str_lst) != 2:
                    print("\n" + "─" * 50)
                    print("❌ Error: No additional arguments required")
                    print("─" * 50 + "\n")
                else:
                    self.report_manager.generate_report_payment_method_usage()
                    self.log_manager.add_log(self.log_manager.generate_log_description("report", ["payment_method_usage"]))
                    
            elif report_type == "tag_expenses":
                if len(cmd_str_lst) != 2:
                    print("\n" + "─" * 50)
                    print("❌ Error: No additional arguments required")
                    print("─" * 50 + "\n")
                else:
                    self.report_manager.generate_report_tag_expenses()
                    self.log_manager.add_log(self.log_manager.generate_log_description("report", ["tag_expenses"]))
                    
            elif report_type == "payment_method_details_expense":
                if len(cmd_str_lst) != 2:
                    print("\n" + "─" * 50)
                    print("❌ Error: No additional arguments required")
                    print("─" * 50 + "\n")
                else:
                    self.report_manager.generate_report_payment_method_details_expense()
                    self.log_manager.add_log(self.log_manager.generate_log_description("report", ["payment_method_details_expense"]))
                    
            elif report_type == "analyze_expenses":
                field_dict = {
                    "amount": [],
                    "date": [],
                    "category": [],
                    "tag": [],
                    "payment_method": [],
                    "month": []
                }
                
                field_op = ["<=",">=","=","<",">"]
                
                # Check if there are filter arguments
                if len(cmd_str_lst) > 2:
                    # Extract everything after "report analyze_expenses"
                    filter_part = cmd_str[cmd_str.find(report_type) + len(report_type):].strip()
                    
                    # Split by comma to get individual constraints
                    constraint_list = filter_part.split(',')
                    
                    for constraint in constraint_list:
                        constraint = constraint.strip()
                        operator_found = False
                        
                        # Try each operator to see if it exists in the constraint
                        for op in field_op:
                            if op in constraint:
                                # Split by operator
                                parts = constraint.split(op, 1)  # Split only on first occurrence
                                if len(parts) == 2:
                                    field = parts[0].strip()
                                    value = parts[1].strip()
                                    
                                    # Validate field
                                    if field not in field_dict:
                                        print("\n" + "─" * 50)
                                        print(f"❌ Error: Invalid field '{field}'")
                                        print("─" * 50 + "\n")
                                        return
                                    
                                    # Add to field_dict
                                    field_dict[field].append([op, value])
                                    operator_found = True
                                    break
                        
                        if not operator_found:
                            print("\n" + "─" * 50)
                            print(f"❌ Error: No valid operator found in filter '{constraint}'")
                            print("─" * 50 + "\n")
                            return
                    
                    self.report_manager.generate_expenses_analytics(field_dict)
                    self.log_manager.add_log(self.log_manager.generate_log_description("report", ["analyze_expenses", filter_part]))
                else:
                    self.report_manager.generate_expenses_analytics()
                    self.log_manager.add_log(self.log_manager.generate_log_description("report", ["analyze_expenses"]))

        elif cmd == "view_logs":
            if self.user_manager.privileges == "admin":
                if len(cmd_str_lst) == 1:
                    # Add spacing before displaying logs
                    print()
                    self.log_manager.display_logs()
                    # Add spacing after displaying logs
                    print()
                    self.log_manager.add_log(self.log_manager.generate_log_description("view_logs", ["all"]))
                elif len(cmd_str_lst) == 2:
                    username = cmd_str_lst[1]
                    # Add spacing before displaying logs
                    print()
                    self.log_manager.display_logs(username=username)
                    # Add spacing after displaying logs
                    print()
                    self.log_manager.add_log(self.log_manager.generate_log_description("view_logs", [username]))
                elif len(cmd_str_lst) == 3 and cmd_str_lst[1] == "--limit":
                    # View logs with limit
                    try:
                        limit = int(cmd_str_lst[2])
                        self.log_manager.display_logs(limit=limit)
                        self.log_manager.add_log(self.log_manager.generate_log_description("view_logs", ["--limit", str(limit)]))
                    except ValueError:
                        print("\n" + "─" * 50)
                        print("❌ Error: Limit must be a number")
                        print("─" * 50 + "\n")
                else:
                    print("\n" + "─" * 50)
                    print(f"❌ Error: Incorrect syntax. Usage: {list_of_privileges['admin']['view_logs']}")
                    print("─" * 50 + "\n")
            else:
                # Regular users cannot view logs at all
                print("\n" + "─" * 50)
                print("❌ Error: The view_logs command is restricted to admin users only")
                print("─" * 50 + "\n")

        else:
            print("\n" + "─" * 50)
            print("❌ Error: Invalid command")
            print("─" * 50 + "\n")
