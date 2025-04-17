# Constants for the expense app

list_of_privileges = {
    "admin": {
        "add_user": "add_user <username> <password> <role>",
        "list_payment_methods": "list_payment_methods",
        "add_payment_method": "add_payment_method <payment_method_name>",
        "list_categories": "list_categories",
        "add_category": "add_category <category_name>",
        "delete_category": "delete_category <category_name>",
        "list_users": "list_users",
        "list_expenses": "list_expenses [<field> <operator> <value>, ...]",
        "view_logs": "view_logs [username | --limit N]",
        "delete_user": "delete_user <username>",
        "report": {
            "top_expenses": "report top_expenses <N> <start_date> <end_date>",
            "category_spending": "report category_spending <category>",
            "above_average_expenses": "report above_average_expenses",
            "monthly_category_spending": "report monthly_category_spending",
            "highest_spender_per_month": "report highest_spender_per_month",
            "frequent_category": "report frequent_category",
            "tag_expenses": "report tag_expenses",
            "payment_method_usage": "report payment_method_usage",
            "analyze_expenses": "report analyze_expenses [<field> <operator> <value>, ...]"
        }
    },
    "user": {
        "list_categories": "list_categories",
        "list_payment_methods": "list_payment_methods",
        "add_expense": "add_expense <amount> <category> <payment_method> <date> <description> <tag>",
        "update_expense": "update_expense <expense_id> <field> <new_value>",
        "delete_expense": "delete_expense <expense_id>",
        "list_expenses": "list_expenses [<field> <operator> <value>, ...]",
        "import_expenses": "import_expenses <file_path>",
        "export_csv": "export_csv <file_path> [, sort-on <field_name>]",
        "delete_user": "delete_user",
        "report": {
            "top_expenses": "report top_expenses <N> <start_date> <end_date>",
            "category_spending": "report category_spending <category>",
            "above_average_expenses": "report above_average_expenses",
            "monthly_category_spending": "report monthly_category_spending",
            "payment_method_usage": "report payment_method_usage",
            "frequent_category": "report frequent_category",
            "tag_expenses": "report tag_expenses",
            "payment_method_details_expense": "report payment_method_details_expense",
            "analyze_expenses": "report analyze_expenses [<field> <operator> <value>, ...]"
        }
    }
}
