# User-related queries
USER_QUERIES = {
    "get_user": "SELECT username, password FROM User WHERE username = ?",
    "get_user_role": """
        SELECT r.role_name
        FROM User_Role ur
        JOIN Role r ON ur.role_id = r.role_id
        WHERE ur.username = ?
    """,
    "get_role_id": "SELECT role_id FROM Role WHERE role_name = ?",
    "insert_user": "INSERT INTO User (username, password) VALUES (?, ?)",
    "insert_user_role": "INSERT INTO User_Role (username, role_id) VALUES (?, ?)",
    "list_users": """
        SELECT u.username, r.role_name
        FROM User u
        JOIN User_Role ur ON u.username = ur.username
        JOIN Role r ON ur.role_id = r.role_id
        ORDER BY u.username
    """,
    "check_user_expenses": "SELECT COUNT(*) FROM User_Expense WHERE username = ?",
    "delete_user_role": "DELETE FROM User_Role WHERE username = ?",
    "delete_user_related": """
        DELETE FROM Logs WHERE username = ?
    """,
    "delete_user": "DELETE FROM User WHERE username = ?"
}

# Category-related queries
CATEGORY_QUERIES = {
    "add_category": "INSERT INTO Categories (category_name) VALUES (?)",
    "list_categories": "SELECT category_name FROM Categories ORDER BY category_name",
    "check_category_expenses": """
        SELECT COUNT(*)
        FROM Category_Expense ce
        JOIN Categories c ON ce.category_id = c.category_id
        WHERE c.category_name = ?
    """,
    "delete_category_related": """
        DELETE FROM Category_Expense
        WHERE category_id IN (SELECT category_id FROM Categories WHERE category_name = ?)
    """,
    "delete_category": "DELETE FROM Categories WHERE category_name = ?"
}

# Payment method-related queries
PAYMENT_QUERIES = {
    "add_payment_method": "INSERT INTO Payment_Method (payment_method_name) VALUES (?)",
    "list_payment_methods": "SELECT payment_method_name FROM Payment_Method ORDER BY payment_method_name",
    "check_payment_expenses": "SELECT COUNT(*) FROM Payment_Method_Expense WHERE payment_method_id = (SELECT payment_method_id FROM Payment_Method WHERE payment_method_name = ?)",
    "delete_payment_related": "DELETE FROM Payment_Method_Expense WHERE payment_method_id = (SELECT payment_method_id FROM Payment_Method WHERE payment_method_name = ?)",
    "delete_payment_method": "DELETE FROM Payment_Method WHERE payment_method_name = ?"
}

# Base query for expense listing
BASE_EXPENSE_QUERY = """
    SELECT 
        e.expense_id,
        e.date,
        e.amount,
        e.description,
        c.category_name,
        t.tag_name,
        pm.payment_method_name,
        ue.username,
        pme.payment_detail_identifier
    FROM 
        Expense e
    LEFT JOIN Category_Expense ce ON e.expense_id = ce.expense_id
    LEFT JOIN Categories c ON ce.category_id = c.category_id
    LEFT JOIN Tag_Expense te ON e.expense_id = te.expense_id
    LEFT JOIN Tags t ON te.tag_id = t.tag_id
    LEFT JOIN Payment_Method_Expense pme ON e.expense_id = pme.expense_id
    LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
    LEFT JOIN User_Expense ue ON e.expense_id = ue.expense_id
"""

# Expense-related queries
EXPENSE_QUERIES = {
    "insert_expense": "INSERT INTO Expense (date, amount, description) VALUES (?, ?, ?)",
    "insert_category_expense": "INSERT INTO Category_Expense (category_id, expense_id) VALUES (?, ?)",
    "insert_tag": "INSERT INTO Tags (tag_name) VALUES (?)",
    "insert_tag_expense": "INSERT INTO Tag_Expense (tag_id, expense_id) VALUES (?, ?)",
    "insert_payment_method_expense": "INSERT INTO Payment_Method_Expense (payment_method_id, expense_id, payment_detail_identifier) VALUES (?, ?, ?)",
    "insert_user_expense": "INSERT INTO User_Expense (username, expense_id) VALUES (?, ?)",
    "check_expense_owner": """
        SELECT COUNT(*) FROM User_Expense 
        WHERE expense_id = ? AND username = ?
    """,
    "update_expense_amount": "UPDATE Expense SET amount = ? WHERE expense_id = ?",
    "update_expense_description": "UPDATE Expense SET description = ? WHERE expense_id = ?",
    "update_expense_date": "UPDATE Expense SET date = ? WHERE expense_id = ?",
    "update_category_expense": """
        UPDATE Category_Expense 
        SET category_id = ? 
        WHERE expense_id = ?
    """,
    "update_tag_expense": """
        UPDATE Tag_Expense 
        SET tag_id = ? 
        WHERE expense_id = ?
    """,
    "update_payment_method_expense": """
        UPDATE Payment_Method_Expense 
        SET payment_method_id = ? 
        WHERE expense_id = ?
    """,
    "delete_category_expense": "DELETE FROM Category_Expense WHERE expense_id = ?",
    "delete_tag_expense": "DELETE FROM Tag_Expense WHERE expense_id = ?",
    "delete_payment_method_expense": "DELETE FROM Payment_Method_Expense WHERE expense_id = ?",
    "delete_user_expense": "DELETE FROM User_Expense WHERE expense_id = ?",
    "delete_expense": "DELETE FROM Expense WHERE expense_id = ?"
}

# Report-related queries
REPORT_QUERIES = {
    "top_expenses": """
        SELECT 
            e.expense_id,
            e.date,
            e.amount,
            e.description,
            c.category_name,
            t.tag_name,
            pm.payment_method_name,
            ue.username
        FROM 
            Expense e
        LEFT JOIN Category_Expense ce ON e.expense_id = ce.expense_id
        LEFT JOIN Categories c ON ce.category_id = c.category_id
        LEFT JOIN Tag_Expense te ON e.expense_id = te.expense_id
        LEFT JOIN Tags t ON te.tag_id = t.tag_id
        LEFT JOIN Payment_Method_Expense pme ON e.expense_id = pme.expense_id
        LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
        LEFT JOIN User_Expense ue ON e.expense_id = ue.expense_id
        WHERE 
            e.date BETWEEN ? AND ?
            {user_filter}
        ORDER BY 
            e.amount DESC
        LIMIT ?
    """,
    "get_category_id": "SELECT category_id FROM Categories WHERE LOWER(category_name) = LOWER(?)",
    "category_spending": """
        SELECT 
            SUM(e.amount) as total,
            COUNT(e.expense_id) as count,
            MAX(e.amount) as max_amount,
            MIN(e.amount) as min_amount,
            AVG(e.amount) as avg_amount
        FROM 
            Expense e
        JOIN Category_Expense ce ON e.expense_id = ce.expense_id
        JOIN User_Expense ue ON e.expense_id = ue.expense_id
        WHERE 
            ce.category_id = ?
            {user_filter}
    """,
    "base_expense_query": BASE_EXPENSE_QUERY
}

# CSV Operation Queries
CSV_QUERIES = {
    "export_base": """
SELECT e.amount,
    c.category_name,
    pm.payment_method_name,
    e.date,
    e.description,
    t.tag_name,
    pme.payment_detail_identifier
FROM Expense e
JOIN Category_Expense ce ON e.expense_id = ce.expense_id
JOIN Categories c ON ce.category_id = c.category_id
JOIN Payment_Method_Expense pme ON e.expense_id = pme.expense_id
JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
JOIN Tag_Expense te ON e.expense_id = te.expense_id
JOIN Tags t ON te.tag_id = t.tag_id
"""
}

# Log Management Queries
LOG_QUERIES = {
    "add_log_with_description": """
        INSERT INTO Logs (username, timestamp, description) 
        VALUES (?, ?, ?)""",
    "get_user_logs": """
        SELECT logid, timestamp, username, description 
        FROM Logs 
        WHERE username = ? 
        ORDER BY timestamp ASC 
        LIMIT ?""",
    "get_all_logs": """
        SELECT logid, timestamp, username, description 
        FROM Logs 
        ORDER BY timestamp ASC 
        LIMIT ?""",
    "view_logs_base": """
        SELECT logid, username, timestamp, description
        FROM Logs""",
    "view_logs_order": " ORDER BY timestamp ASC",
    "get_users_with_logs": """
        SELECT DISTINCT username FROM Logs ORDER BY username
    """
}
