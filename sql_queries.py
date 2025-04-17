"""
Centralized repository for SQL queries used in the expense tracking application.
This helps improve security by separating SQL code from application logic.
"""

# User Management Queries
USER_QUERIES = {
    "get_user": "SELECT username, password FROM User WHERE username = ?",
    "get_user_role": "SELECT r.role_name FROM Role r JOIN user_role ur ON r.role_id = ur.role_id WHERE ur.username = ?",
    "insert_user": "INSERT INTO User (username, password) VALUES (?, ?)",
    "insert_user_role": "INSERT INTO user_role (username, role_id) VALUES (?, ?)",
    "get_role_id": "SELECT role_id FROM Role WHERE role_name = ?",
    "list_users": "SELECT username, role_name FROM user_role u, role r WHERE u.role_id = r.role_id",
    "delete_user": "DELETE FROM User WHERE username = ?",
    "delete_user_related": "DELETE FROM user_expense WHERE username = ?",
    "delete_user_role": "DELETE FROM user_role WHERE username = ?",
    "check_user_expenses": "SELECT COUNT(*) FROM user_expense WHERE username = ?"
}

# Category Management Queries
CATEGORY_QUERIES = {
    "add_category": "INSERT INTO categories (category_name) VALUES (?)",
    "get_category_by_name": "SELECT category_id FROM Categories WHERE category_name = ?",
    "list_categories": "SELECT category_name FROM categories",
    "delete_category": "DELETE FROM Categories WHERE category_name = ?",
    "delete_category_related": "DELETE FROM category_expense WHERE category_id = (SELECT category_id FROM Categories WHERE category_name = ?)",
    "check_category_expenses": "SELECT COUNT(*) FROM category_expense WHERE category_id = (SELECT category_id FROM Categories WHERE category_name = ?)"
}

# Payment Method Queries
PAYMENT_QUERIES = {
    "add_payment_method": "INSERT INTO Payment_Method (payment_method_name) VALUES (?)",
    "get_payment_method_by_name": "SELECT payment_method_id FROM Payment_Method WHERE Payment_Method_Name = ?",
    "list_payment_methods": "SELECT payment_method_name FROM Payment_Method"
}

# Expense Management Queries
EXPENSE_QUERIES = {
    "insert_expense": "INSERT INTO Expense (date, amount, description) VALUES (?, ?, ?)",
    "insert_category_expense": "INSERT INTO category_expense (category_id, expense_id) VALUES (?, ?)",
    "insert_tag": "INSERT INTO Tags (tag_name) VALUES (?)",
    "get_tag": "SELECT tag_id FROM Tags WHERE tag_name = ?",
    "insert_tag_expense": "INSERT INTO tag_expense (tag_id, expense_id) VALUES (?, ?)",
    "insert_payment_method_expense": "INSERT INTO payment_method_expense (payment_method_id, expense_id, payment_detail_identifier) VALUES (?, ?, ?)",
    "insert_user_expense": "INSERT INTO user_expense (username, expense_id) VALUES (?, ?)",
    "check_expense_owner": "SELECT COUNT(*) FROM user_expense WHERE expense_id = ? AND username = ?",
    "update_expense_amount": "UPDATE Expense SET amount = ? WHERE expense_id = ?",
    "update_expense_description": "UPDATE Expense SET description = ? WHERE expense_id = ?",
    "update_expense_date": "UPDATE Expense SET date = ? WHERE expense_id = ?",
    "update_category_expense": "UPDATE category_expense SET category_id = ? WHERE expense_id = ?",
    "update_tag_expense": "UPDATE tag_expense SET tag_id = ? WHERE expense_id = ?",
    "update_payment_method_expense": "UPDATE payment_method_expense SET payment_method_id = ? WHERE expense_id = ?",
    "delete_category_expense": "DELETE FROM category_expense WHERE expense_id = ?",
    "delete_tag_expense": "DELETE FROM tag_expense WHERE expense_id = ?",
    "delete_payment_method_expense": "DELETE FROM payment_method_expense WHERE expense_id = ?",
    "delete_user_expense": "DELETE FROM user_expense WHERE expense_id = ?",
    "delete_expense": "DELETE FROM Expense WHERE expense_id = ?"
}

# Base queries for list_expenses and reports
BASE_EXPENSE_QUERY = """
SELECT e.expense_id, e.date, e.amount, e.description, 
    c.category_name, t.tag_name, pm.payment_method_name, ue.username
FROM Expense e
LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
LEFT JOIN Categories c ON ce.category_id = c.category_id
LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
LEFT JOIN Tags t ON te.tag_id = t.tag_id
LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
"""

# Reporting Queries
REPORT_QUERIES = {
    "base_expense_query": """
    SELECT e.expense_id, e.date, e.amount, e.description, 
        c.category_name, t.tag_name, pm.payment_method_name, ue.username,
        pme.payment_detail_identifier
    FROM Expense e
    LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
    LEFT JOIN Categories c ON ce.category_id = c.category_id
    LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
    LEFT JOIN Tags t ON te.tag_id = t.tag_id
    LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
    LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
    LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
    """,
    
    "get_category_id": "SELECT category_id FROM Categories WHERE category_name = ?",
    
    "top_expenses": BASE_EXPENSE_QUERY + """
    WHERE e.date BETWEEN ? AND ?
    {user_filter}
    ORDER BY e.amount DESC LIMIT ?
    """,
    
    "category_spending": """
    SELECT SUM(e.amount) as total_amount, 
           COUNT(e.expense_id) as count, 
           MAX(e.amount) as max_expense, 
           MIN(e.amount) as min_expense,
           AVG(e.amount) as avg_expense
    FROM Expense e
    JOIN category_expense ce ON e.expense_id = ce.expense_id
    JOIN user_expense ue ON e.expense_id = ue.expense_id
    WHERE ce.category_id = ?
    {user_filter}
    """,
    
    "payment_method_details": """
    SELECT pme.payment_detail_identifier, 
           COUNT(e.expense_id) as usage_count, 
           SUM(e.amount) as total_amount,
           AVG(e.amount) as avg_amount,
           pm.payment_method_name
    FROM Expense e
    JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
    JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
    JOIN user_expense ue ON e.expense_id = ue.expense_id
    WHERE pme.payment_detail_identifier IS NOT NULL 
    AND pme.payment_detail_identifier != ''
    AND ue.username = ?
    GROUP BY pme.payment_detail_identifier ORDER BY usage_count DESC
    """,
    
    "payment_method_usage": """
    SELECT pm.payment_method_name, COUNT(pme.expense_id) as usage_count, 
           SUM(e.amount) as total_amount
    FROM Payment_Method pm
    JOIN payment_method_expense pme ON pm.payment_method_id = pme.payment_method_id
    JOIN Expense e ON pme.expense_id = e.expense_id
    JOIN user_expense ue ON e.expense_id = ue.expense_id
    {user_filter}
    GROUP BY pm.payment_method_name
    ORDER BY total_amount DESC
    """,
    
    "frequent_category": """
    SELECT c.category_name, COUNT(ce.expense_id) as usage_count, SUM(e.amount) as total_amount
    FROM Categories c
    JOIN category_expense ce ON c.category_id = ce.category_id
    JOIN Expense e ON ce.expense_id = e.expense_id
    JOIN user_expense ue ON e.expense_id = ue.expense_id
    {user_filter}
    GROUP BY c.category_name ORDER BY usage_count DESC
    """,
    
    "highest_spender_per_month": """
    WITH MonthlyUserSpending AS (
        SELECT 
            strftime('%Y-%m', e.date) as month,
            ue.username,
            SUM(e.amount) as total_spending
        FROM Expense e
        JOIN user_expense ue ON e.expense_id = ue.expense_id
        GROUP BY month, ue.username
    ),
    RankedSpending AS (
        SELECT 
            month,
            username,
            total_spending,
            RANK() OVER (PARTITION BY month ORDER BY total_spending DESC) as spending_rank
        FROM MonthlyUserSpending
    )
    SELECT 
        month,
        username,
        total_spending
    FROM RankedSpending
    WHERE spending_rank = 1
    ORDER BY month
    """,
    
    "monthly_category_spending": """
    SELECT strftime('%Y-%m', e.date) as month, 
           c.category_name, 
           SUM(e.amount) as total,
           COUNT(e.expense_id) as count
    FROM Expense e
    JOIN category_expense ce ON e.expense_id = ce.expense_id
    JOIN Categories c ON ce.category_id = c.category_id
    JOIN user_expense ue ON e.expense_id = ue.expense_id
    {user_filter}
    GROUP BY month, c.category_name ORDER BY month, total DESC
    """,
    
    "above_average_expenses": """
    WITH CategoryAverages AS (
        SELECT ce.category_id, c.category_name, AVG(e.amount) as avg_amount
        FROM category_expense ce
        JOIN Expense e ON ce.expense_id = e.expense_id
        JOIN Categories c ON ce.category_id = c.category_id
        JOIN user_expense ue ON e.expense_id = ue.expense_id
        {user_filter_subquery}
        GROUP BY ce.category_id
    )
    SELECT e.expense_id, e.date, e.amount, e.description, 
           c.category_name, ca.avg_amount, t.tag_name, 
           pm.payment_method_name, ue.username
    FROM Expense e
    JOIN category_expense ce ON e.expense_id = ce.expense_id
    JOIN Categories c ON ce.category_id = c.category_id
    JOIN CategoryAverages ca ON ce.category_id = ca.category_id
    LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
    LEFT JOIN Tags t ON te.tag_id = t.tag_id
    LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
    LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
    JOIN user_expense ue ON e.expense_id = ue.expense_id
    WHERE e.amount > ca.avg_amount
    {user_filter}
    """,
    
    "tag_expenses": """
    SELECT t.tag_name, COUNT(te.expense_id) as usage_count, SUM(e.amount) as total_amount
    FROM Tags t
    JOIN tag_expense te ON t.tag_id = te.tag_id
    JOIN Expense e ON te.expense_id = e.expense_id
    JOIN user_expense ue ON e.expense_id = ue.expense_id
    {user_filter}
    GROUP BY t.tag_name ORDER BY usage_count DESC
    """
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
JOIN category_expense ce ON e.expense_id = ce.expense_id
JOIN Categories c ON ce.category_id = c.category_id
JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
JOIN tag_expense te ON e.expense_id = te.expense_id
JOIN Tags t ON te.tag_id = t.tag_id
"""
}

# Log Management Queries
LOG_QUERIES = {
    "add_log": "INSERT INTO Logs (username, description) VALUES (?, ?)",
    "get_user_logs": "SELECT logid, timestamp, username, description FROM Logs WHERE username = ? ORDER BY timestamp DESC LIMIT ?",
    "get_all_logs": "SELECT logid, timestamp, username, description FROM Logs ORDER BY timestamp DESC LIMIT ?"
}
