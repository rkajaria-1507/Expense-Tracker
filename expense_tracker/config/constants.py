# List of privileges and available commands for each role
list_of_privileges = {
    "admin": {
        "login": "login <username> <password>",
        "logout": "logout",
        "adduser": "adduser <username> <password> <role>",
        "listusers": "listusers",
        "deleteuser": "deleteuser <username>",
        "addcategory": "addcategory <category_name>",
        "listcategories": "listcategories",
        "deletecategory": "deletecategory <category_name>",
        "addpayment": "addpayment <payment_method>",
        "listpayments": "listpayments",
        "addexpense": "addexpense <amount> <category> <payment_method> <date> <description> <tag> [payment_detail]",
        "listexpenses": "listexpenses [filters...]",
        "updateexpense": "updateexpense <expense_id> <field> <new_value>",
        "deleteexpense": "deleteexpense <expense_id>",
        "exportexpenses": "exportexpenses <file_path>",
        "importexpenses": "importexpenses <file_path> <username>",
        "viewlogs": "viewlogs [username=<username>] [type=<activity_type>] [start=<start_date>] [end=<end_date>]",
        "report": {
            "topexpenses": "report topexpenses <n> <start_date> <end_date>",
            "categoryspending": "report categoryspending <category>",
            "analytics": "report analytics [filters...]"
        }
    },
    "user": {
        "login": "login <username> <password>",
        "logout": "logout",
        "listcategories": "listcategories",
        "listpayments": "listpayments",
        "addexpense": "addexpense <amount> <category> <payment_method> <date> <description> <tag> [payment_detail]",
        "listexpenses": "listexpenses [filters...]",
        "updateexpense": "updateexpense <expense_id> <field> <new_value>",
        "deleteexpense": "deleteexpense <expense_id>",
        "exportexpenses": "exportexpenses <file_path>",
        "report": {
            "topexpenses": "report topexpenses <n> <start_date> <end_date>",
            "categoryspending": "report categoryspending <category>",
            "analytics": "report analytics [filters...]"
        }
    }
}