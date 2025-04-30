import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import os
from expense_tracker.database.sql_queries import REPORT_QUERIES
import pandas as pd

class ReportManager:
    def __init__(self, cursor, conn):
        self.conn = conn
        self.cursor = cursor
        self.current_user = None
        self.privileges = None
    
    def set_user_info(self, username, privileges):
        self.current_user = username
        self.privileges = privileges
    
    def _mask_payment_details(self, details):
        """Mask payment method details for privacy"""
        if not details or len(details) < 4:
            return details
        
        # Mask most of the characters, leaving only the last 4
        masked_detail = f"{details[:2]}{'*' * (len(details) - 4)}{details[-2:]}"
        return masked_detail
        
    def get_category_statistics(self, category):
        """Get statistics for a specific category"""
        try:
            # Check if category exists
            self.cursor.execute("SELECT category_id FROM Categories WHERE category_name = ?", (category,))
            result = self.cursor.fetchone()
            if result is None:
                return None
                
            category_id = result[0]
            
            # Create query based on privileges
            if self.privileges != "admin":
                query = """
                    SELECT 
                        SUM(e.amount) as total,
                        COUNT(e.expense_id) as count,
                        AVG(e.amount) as average,
                        MAX(e.amount) as max_amount,
                        MIN(e.amount) as min_amount
                    FROM 
                        Expense e
                        JOIN category_expense ce ON e.expense_id = ce.expense_id
                        JOIN user_expense ue ON e.expense_id = ue.expense_id
                    WHERE 
                        ce.category_id = ? AND ue.username = ?
                """
                params = (category_id, self.current_user)
            else:
                query = """
                    SELECT 
                        SUM(e.amount) as total,
                        COUNT(e.expense_id) as count,
                        AVG(e.amount) as average,
                        MAX(e.amount) as max_amount,
                        MIN(e.amount) as min_amount
                    FROM 
                        Expense e
                        JOIN category_expense ce ON e.expense_id = ce.expense_id
                    WHERE 
                        ce.category_id = ?
                """
                params = (category_id,)
            
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()
            
            # Return None if no data found
            if result[0] is None:
                return None
                
            # Add category name to result
            stats = {
                "category": category,
                "total": result[0],
                "count": result[1],
                "average": result[2],
                "max_amount": result[3],
                "min_amount": result[4]
            }
            
            # Get monthly spending for this category
            if self.privileges != "admin":
                monthly_query = """
                    SELECT 
                        strftime('%Y-%m', e.date) as month,
                        SUM(e.amount) as amount
                    FROM 
                        Expense e
                        JOIN category_expense ce ON e.expense_id = ce.expense_id
                        JOIN user_expense ue ON e.expense_id = ue.expense_id
                    WHERE 
                        ce.category_id = ? AND ue.username = ?
                    GROUP BY 
                        month
                    ORDER BY 
                        month ASC
                """
                self.cursor.execute(monthly_query, params)
            else:
                monthly_query = """
                    SELECT 
                        strftime('%Y-%m', e.date) as month,
                        SUM(e.amount) as amount
                    FROM 
                        Expense e
                        JOIN category_expense ce ON e.expense_id = ce.expense_id
                    WHERE 
                        ce.category_id = ?
                    GROUP BY 
                        month
                    ORDER BY 
                        month ASC
                """
                self.cursor.execute(monthly_query, (category_id,))
                
            monthly_data = self.cursor.fetchall()
            stats["monthly_data"] = [(month, amount) for month, amount in monthly_data]
            
            # Get recent transactions
            if self.privileges != "admin":
                recent_query = """
                    SELECT 
                        e.expense_id,
                        e.date,
                        e.amount,
                        e.description
                    FROM 
                        Expense e
                        JOIN category_expense ce ON e.expense_id = ce.expense_id
                        JOIN user_expense ue ON e.expense_id = ue.expense_id
                    WHERE 
                        ce.category_id = ? AND ue.username = ?
                    ORDER BY 
                        e.date DESC
                    LIMIT 5
                """
                self.cursor.execute(recent_query, params)
            else:
                recent_query = """
                    SELECT 
                        e.expense_id,
                        e.date,
                        e.amount,
                        e.description,
                        ue.username
                    FROM 
                        Expense e
                        JOIN category_expense ce ON e.expense_id = ce.expense_id
                        JOIN user_expense ue ON e.expense_id = ue.expense_id
                    WHERE 
                        ce.category_id = ?
                    ORDER BY 
                        e.date DESC
                    LIMIT 5
                """
                self.cursor.execute(recent_query, (category_id,))
                
            recent_transactions = self.cursor.fetchall()
            
            if self.privileges == "admin":
                stats["recent_transactions"] = [
                    {"id": tx[0], "date": tx[1], "amount": tx[2], "description": tx[3], "username": tx[4]}
                    for tx in recent_transactions
                ]
            else:
                stats["recent_transactions"] = [
                    {"id": tx[0], "date": tx[1], "amount": tx[2], "description": tx[3]}
                    for tx in recent_transactions
                ]
            
            return stats
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        except Exception as e:
            print(f"Error getting category statistics: {e}")
            return None
            
    def get_expenses_by_date_range(self, start_date, end_date):
        """Get all expenses within a date range as a pandas DataFrame"""
        try:
            # Validate date format
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
            
            # Create query based on privileges
            base_query = """
                SELECT 
                    e.expense_id, 
                    e.date, 
                    e.amount, 
                    e.description, 
                    c.category_name as category, 
                    t.tag_name as tag, 
                    pm.payment_method_name as payment_method
                FROM 
                    Expense e
                    LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                    LEFT JOIN Categories c ON ce.category_id = c.category_id
                    LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
                    LEFT JOIN Tags t ON te.tag_id = t.tag_id
                    LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
                    LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                    JOIN user_expense ue ON e.expense_id = ue.expense_id
                WHERE 
                    e.date BETWEEN ? AND ?
            """
            
            if self.privileges != "admin":
                base_query += " AND ue.username = ?"
                params = (start_date, end_date, self.current_user)
            else:
                params = (start_date, end_date)
            
            # Execute query and convert to DataFrame
            expenses_df = pd.read_sql_query(base_query, self.conn, params=params)
            return expenses_df
            
        except (sqlite3.Error, ValueError) as e:
            print(f"Error: {e}")
            return pd.DataFrame()  # Return empty DataFrame on error
            
    def get_category_expenses_by_date_range(self, category, start_date, end_date):
        """Get expenses for a specific category within a date range as a DataFrame"""
        try:
            # Validate date format
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
            
            # Create query based on privileges
            base_query = """
                SELECT 
                    e.expense_id, 
                    e.date, 
                    e.amount, 
                    e.description
                FROM 
                    Expense e
                    JOIN category_expense ce ON e.expense_id = ce.expense_id
                    JOIN Categories c ON ce.category_id = c.category_id
                    JOIN user_expense ue ON e.expense_id = ue.expense_id
                WHERE 
                    e.date BETWEEN ? AND ?
                    AND c.category_name = ?
            """
            
            if self.privileges != "admin":
                base_query += " AND ue.username = ?"
                params = (start_date, end_date, category, self.current_user)
            else:
                params = (start_date, end_date, category)
            
            # Execute query and convert to DataFrame
            expenses_df = pd.read_sql_query(base_query, self.conn, params=params)
            return expenses_df
            
        except (sqlite3.Error, ValueError) as e:
            print(f"Error: {e}")
            return pd.DataFrame()  # Return empty DataFrame on error
    
    # ...existing code...
    
    def generate_report_top_expenses(self, n, start_date, end_date):
        """Report top N expenses for a given date range"""
        try:
            n = int(n)
            if n <= 0:
                print("Error: N must be a positive integer")
                return

            # Validate date format
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                print("Error: Dates must be in the format YYYY-MM-DD")
                return

            # Use query from sql_queries.py
            query = REPORT_QUERIES["top_expenses"]
            if self.privileges != "admin":
                query = query.format(user_filter="AND ue.username = ?")
                params = [start_date, end_date, self.current_user, n]
            else:
                query = query.format(user_filter="")
                params = [start_date, end_date, n]
            
            # Execute query
            self.cursor.execute(query, params)
            expenses = self.cursor.fetchall()

            if not expenses:
                print(f"No expenses found between {start_date} and {end_date}")
                return

            # Display results
            print(f"\nTop {n} Expenses from {start_date} to {end_date}:")
            print("-" * 95)
            
            # Different headers based on user role
            if self.privileges == "admin":
                print(f"{'ID':<5} {'Username':<15} {'Date':<12} {'Amount':<10} {'Category':<15} {'Tag':<15} {'Payment Method':<15} {'Description':<25}")
                print("-" * 95)
                
                for expense in expenses:
                    expense_id, date, amount, description, category, tag, payment_method, username = expense
                    category = category or "N/A"
                    tag = tag or "N/A"
                    username = username or "N/A"
                    payment_method = payment_method or "N/A"
                    description = (description[:22] + "...") if description and len(description) > 25 else (description or "")
                    
                    print(f"{expense_id:<5} {username:<15} {date:<12} {amount:<10.2f} {category:<15} {tag:<15} {payment_method:<15} {description:<25}")
            else:
                print(f"{'ID':<5} {'Date':<12} {'Amount':<10} {'Category':<15} {'Tag':<15} {'Payment Method':<15} {'Description':<25}")
                print("-" * 95)
                
                for expense in expenses:
                    expense_id, date, amount, description, category, tag, payment_method, _ = expense
                    category = category or "N/A"
                    tag = tag or "N/A"
                    payment_method = payment_method or "N/A"
                    description = (description[:22] + "...") if description and len(description) > 25 else (description or "")
                    
                    print(f"{expense_id:<5} {date:<12} {amount:<10.2f} {category:<15} {tag:<15} {payment_method:<15} {description:<25}")
            
            print("-" * 95)
            print(f"Total: {len(expenses)} expense(s) found. Total amount: {sum(expense[2] for expense in expenses):.2f}")
            
            # Create a line chart showing just expense amounts
            if expenses:
                plt.figure(figsize=(12, 6))
                
                # Extract data for plotting
                ids = [str(exp[0]) for exp in expenses]
                amounts = [exp[2] for exp in expenses]
                
                # Create line chart
                plt.plot(ids, amounts, marker='o', linestyle='-', color='red', linewidth=2, markersize=8)
                
                # Add amount labels above each point
                for i, amount in enumerate(amounts):
                    plt.text(i, amount + (max(amounts) * 0.02), f'{amount:.2f}', 
                            ha='center', va='bottom', fontsize=9)
                
                plt.xlabel('Expense ID')
                plt.ylabel('Amount')
                
                # Add username information for admin users
                if self.privileges == "admin":
                    # Add username labels below each point
                    usernames = [exp[7] or "N/A" for exp in expenses]
                    plt.title(f'Top {n} Expenses - Line Chart (With User Info)')
                    
                    # Add custom x-tick labels with ID and username
                    plt.xticks(range(len(ids)), [f"ID:{id}\n{user}" for id, user in zip(ids, usernames)], rotation=45)
                else:
                    plt.title(f'Top {n} Expenses - Line Chart')
                    plt.xticks(rotation=45)
                
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.tight_layout()
                
                plt.show(block=False)  # Non-blocking display
                plt.pause(0.001)  # Small pause to render the plot
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")

    # ...rest of the methods...
    
    def generate_report_category_spending(self, category):
        """Report total spending for a specific category"""
        try:
            # Normalize category name
            category = category.strip().lower()
            
            # Check if category exists
            self.cursor.execute(REPORT_QUERIES["get_category_id"], (category,))
            result = self.cursor.fetchone()
            if result is None:
                print(f"Error: Category '{category}' does not exist.")
                return
                
            category_id = result[0]
            
            # Use query from sql_queries.py
            query = REPORT_QUERIES["category_spending"]
            if self.privileges != "admin":
                query = query.format(user_filter="AND ue.username = ?")
                params = [category_id, self.current_user]
            else:
                query = query.format(user_filter="")
                params = [category_id]
            
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()
            
            if not result or result[0] is None:
                print(f"No expenses found for category '{category}'")
                return
                
            total, count, max_exp, min_exp, avg_exp = result
            
            # Display results
            print(f"\nSummary Statistics for Category: {category}")
            print("-" * 60)
            print(f"Total spending: {total:.2f}")
            print(f"Number of expenses: {count}")
            print(f"Highest expense: {max_exp:.2f}")
            print(f"Lowest expense: {min_exp:.2f}")
            print(f"Average expense: {avg_exp:.2f}")
            print("-" * 60)
            
            # After displaying text results, add visualization:
            if result and result[0] is not None:
                total, count, max_exp, min_exp, avg_exp = result
                
                # First, get data for category proportion calculation
                if self.privileges != "admin":
                    self.cursor.execute("SELECT SUM(e.amount) FROM Expense e JOIN user_expense ue ON e.expense_id = ue.expense_id WHERE ue.username = ?", 
                                       (self.current_user,))
                else:
                    self.cursor.execute("SELECT SUM(e.amount) FROM Expense e")
                    
                total_all_expenses = self.cursor.fetchone()[0] or 0
                percentage = (total / total_all_expenses * 100) if total_all_expenses > 0 else 0
                
                # Create a dashboard layout with multiple subplots
                fig = plt.figure(figsize=(12, 8))
                plt.suptitle(f'Dashboard: {category.capitalize()} Category', fontsize=16)
                
                # Grid spec for custom layout
                gs = fig.add_gridspec(2, 3)
                
                # First subplot: Key Metrics display
                ax1 = fig.add_subplot(gs[0, 0])
                ax1.axis('off')  # No axes for text display
                ax1.text(0.5, 0.9, f"Key Metrics", ha='center', fontsize=14, fontweight='bold')
                ax1.text(0.5, 0.7, f"Total Spending: ${total:.2f}", ha='center')
                ax1.text(0.5, 0.5, f"Number of Expenses: {count}", ha='center')
                ax1.text(0.5, 0.3, f"Average Expense: ${avg_exp:.2f}", ha='center')
                
                # Second subplot: Value comparison bar chart
                ax2 = fig.add_subplot(gs[0, 1:])
                metrics = ['Total', 'Maximum', 'Minimum', 'Average']
                values = [total, max_exp, min_exp, avg_exp]
                colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
                bars = ax2.bar(metrics, values, color=colors)
                ax2.set_title('Expense Values')
                ax2.set_ylabel('Amount ($)')
                
                # Add value labels to the bars
                for bar in bars:
                    height = bar.get_height()
                    ax2.annotate(f'${height:.2f}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),  # 3 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom')
                
                # Third subplot: Pie chart showing proportion
                ax3 = fig.add_subplot(gs[1, 0])
                sizes = [total, total_all_expenses - total]
                labels = [f'{category.capitalize()}\n(${total:.2f})', f'Other Categories\n(${total_all_expenses - total:.2f})']
                colors = ['#3498db', '#e6e6e6']
                explode = (0.1, 0)  # explode the first slice
                
                # Only create pie if there are other expenses
                if total_all_expenses > 0:
                    ax3.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                           shadow=True, startangle=90)
                    ax3.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                    ax3.set_title('Proportion of Total Spending')
                else:
                    ax3.axis('off')
                    ax3.text(0.5, 0.5, "No data for proportion", ha='center')
                
                # Fourth subplot: Gauge chart for percentage of total
                ax4 = fig.add_subplot(gs[1, 1:])
                gauge_colors = ['#f1c40f', '#e67e22', '#e74c3c']
                
                # Create a semi-circle gauge
                theta = np.linspace(0, np.pi, 100)
                r = 1.0
                
                # Draw the gauge background
                for i, color in enumerate(gauge_colors):
                    ax4.fill_between(theta, 0.8, 1.0, 
                                    color=color, 
                                    alpha=0.3,
                                    where=((i/3)*np.pi <= theta) & (theta <= ((i+1)/3)*np.pi))
                
                # Draw the gauge needle
                needle_theta = np.pi * min(percentage/100, 1.0)
                ax4.plot([0, np.cos(needle_theta)], [0, np.sin(needle_theta)], 'k-', lw=2)
                
                # Add a center circle for gauge aesthetics
                circle = plt.Circle((0, 0), 0.1, color='k', fill=True)
                ax4.add_artist(circle)
                
                # Set gauge labels
                ax4.text(-0.2, -0.15, '0%', fontsize=10)
                ax4.text(1.1, -0.15, '100%', fontsize=10)
                ax4.text(0.5, 0.5, f'{percentage:.1f}%', ha='center', fontsize=14)
                
                # Clean up gauge appearance
                ax4.set_xlim(-1.1, 1.1)
                ax4.set_ylim(-0.2, 1.1)
                ax4.axis('off')
                ax4.set_title('Percentage of Total Spending')
                
                plt.tight_layout()
                plt.subplots_adjust(top=0.9)  # Adjust for main title
                
                # Display the dashboard
                plt.show(block=False)  # Non-blocking display
                plt.pause(0.001)  # Small pause to render the plot
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")

    # ...remaining methods...
    
    def generate_expenses_analytics(self, filters=None):
        """Generate a dashboard with analytics for expenses using the same filtering logic as list_expenses"""
        try:
            # Build query dynamically as in the original code, but start with base query from sql_queries
            query = REPORT_QUERIES["base_expense_query"]
            params = []
            
            # Check if current user is admin or regular user
            if self.privileges != "admin":
                # Regular user can only see their own expenses
                query += """
                WHERE e.expense_id IN (
                    SELECT expense_id FROM user_expense WHERE username = ?
                )
                """
                params.append(self.current_user)
            
            # Define operation fields - SAME as list_expenses
            op_fields = {"and": ["amount", "date"], 
                        "or": ["category", "tag", "payment_method", "month"]}
            
            # Month name to number mapping - SAME as list_expenses
            month_mapping = {
                "january": "01", "february": "02", "march": "03", "april": "04",
                "may": "05", "june": "06", "july": "07", "august": "08",
                "september": "09", "october": "10", "november": "11", "december": "12"
            }
            
            # Process filters - SAME LOGIC as list_expenses
            if filters:
                for field in filters:
                    if not filters[field]:  # Skip empty filter lists
                        continue
                        
                    if field in op_fields["and"]:
                        op = "AND"
                    else:
                        op = "OR"
                        
                    # Special handling for month - SAME as list_expenses
                    if field == "month":
                        connector = "WHERE" if "WHERE" not in query else "AND"
                        query += f" {connector} ("
                        first = True
                        for constraint in filters[field]:
                            op_type, value = constraint
                            if not first:
                                query += f" {op} "
                            first = False
                            
                            # Handle month name conversion
                            if isinstance(value, str) and value.lower() in month_mapping:
                                month_num = month_mapping[value.lower()]
                                query += f"strftime('%m', e.date) {op_type} ?"
                                params.append(month_num)
                            else:
                                # Assume it's a number
                                query += f"strftime('%m', e.date) {op_type} ?"
                                # Ensure month is zero-padded
                                if isinstance(value, str) and len(value) == 1:
                                    params.append(value.zfill(2))
                                else:
                                    params.append(value)
                        query += ")"
                        continue
                        
                    # Handle regular fields with mapping to actual DB columns - SAME as list_expenses
                    field_mapping = {
                        "amount": "e.amount",
                        "date": "e.date",
                        "category": "c.category_name",
                        "tag": "t.tag_name",
                        "payment_method": "pm.payment_method_name"
                    }
                    
                    db_field = field_mapping.get(field, field)
                    
                    connector = "WHERE" if "WHERE" not in query else "AND"
                    query += f" {connector} ("
                    first = True
                    for constraint in filters[field]:
                        op_type, value = constraint
                        if not first:
                            query += f" {op} "
                        first = False
                        query += f"{db_field} {op_type} ?"
                        params.append(value)
                    query += ")"
            
            # Order by date descending - common practice in expense reports
            query += " ORDER BY e.date DESC"
            
            # Execute the query and fetch results
            self.cursor.execute(query, params)
            expenses = self.cursor.fetchall()
            
            if not expenses:
                print("No expenses found matching the criteria.")
                return
            
            # Display summary information
            total_amount = sum(expense[2] for expense in expenses)
            avg_amount = total_amount / len(expenses)
            max_amount = max(expense[2] for expense in expenses)
            min_amount = min(expense[2] for expense in expenses)
            
            print("\nExpense Analytics Dashboard")
            print("-" * 80)
            print(f"Total expenses found: {len(expenses)}")
            print(f"Total amount: ${total_amount:.2f}")
            print(f"Average amount: ${avg_amount:.2f}")
            print(f"Maximum amount: ${max_amount:.2f}")
            print(f"Minimum amount: ${min_amount:.2f}")
            print("-" * 80)
            
            # Prepare data for visualizations
            categories = {}
            payment_methods = {}
            tags = {}
            dates = {}
            months = {}
            
            for expense in expenses:
                expense_id, date, amount, description, category, tag, payment_method, username, payment_detail = expense
                
                # Group by date (for time series)
                year_month = date[:7]  # Extract YYYY-MM
                if year_month not in dates:
                    dates[year_month] = 0
                dates[year_month] += amount
                
                # Also group by month name for month-based analysis
                month_num = date[5:7]  # Extract MM
                month_name = next((k for k, v in month_mapping.items() if v == month_num), month_num)
                if month_name not in months:
                    months[month_name] = 0
                months[month_name] += amount
                
                # Group by category
                if category:
                    if category not in categories:
                        categories[category] = {"count": 0, "total": 0}
                    categories[category]["count"] += 1
                    categories[category]["total"] += amount
                
                # Group by payment method
                if payment_method:
                    if payment_method not in payment_methods:
                        payment_methods[payment_method] = {"count": 0, "total": 0}
                    payment_methods[payment_method]["count"] += 1
                    payment_methods[payment_method]["total"] += amount
                
                # Group by tag
                if tag:
                    if tag not in tags:
                        tags[tag] = {"count": 0, "total": 0}
                    tags[tag]["count"] += 1
                    tags[tag]["total"] += amount
            
            # Create visualizations
            import matplotlib.pyplot as plt
            from matplotlib.gridspec import GridSpec
            import numpy as np
            from matplotlib.ticker import FuncFormatter
            
            # Create figure with six panels using GridSpec for flexible layout
            fig = plt.figure(figsize=(15, 12))
            gs = GridSpec(3, 6, figure=fig)
            
            plt.suptitle('Expense Analytics Dashboard', fontsize=16, fontweight='bold')
            
            # 1. Key Metrics Panel
            ax_metrics = fig.add_subplot(gs[0, :2])
            ax_metrics.axis('off')
            
            # Add a styled metrics panel with key statistics
            metrics_text = (
                f"EXPENSE SUMMARY\n\n"
                f"Total: ${total_amount:.2f}\n"
                f"Average: ${avg_amount:.2f}\n"
                f"Maximum: ${max_amount:.2f}\n"
                f"Minimum: ${min_amount:.2f}\n"
                f"Count: {len(expenses)}\n"
            )
            
            ax_metrics.text(0.5, 0.5, metrics_text, 
                        ha='center', va='center', 
                        fontsize=12,
                        bbox=dict(boxstyle="round,pad=0.5", 
                                    facecolor='lightblue', 
                                    alpha=0.3))
            
            # 2. Spending Time Series
            ax_time = fig.add_subplot(gs[0, 2:])
            
            # Sort dates for time series
            sorted_dates = sorted(dates.keys())
            amounts_by_date = [dates[date] for date in sorted_dates]
            
            # Plot time series
            ax_time.plot(sorted_dates, amounts_by_date, marker='o', linewidth=2, color='blue')
            ax_time.set_title('Spending Over Time')
            ax_time.set_xlabel('Month')
            ax_time.set_ylabel('Amount ($)')
            ax_time.tick_params(axis='x', rotation=45)
            ax_time.grid(True, linestyle='--', alpha=0.7)
            
            # Format y-axis as currency
            ax_time.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x:.0f}'))
            
            # 3. Category Breakdown - Pie Chart
            ax_cat_pie = fig.add_subplot(gs[1, :3])
            
            if categories:
                cat_names = list(categories.keys())
                cat_totals = [categories[cat]["total"] for cat in cat_names]
                
                # Create pie chart
                wedges, texts, autotexts = ax_cat_pie.pie(
                    cat_totals, 
                    labels=cat_names,
                    autopct='%1.1f%%',
                    startangle=90,
                    wedgeprops={'edgecolor': 'w', 'linewidth': 1}
                )
                
                # Style the percentage text
                for autotext in autotexts:
                    autotext.set_fontsize(9)
                    autotext.set_fontweight('bold')
                    
                ax_cat_pie.set_title('Spending by Category')
                ax_cat_pie.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            else:
                ax_cat_pie.text(0.5, 0.5, "No category data available", ha='center', va='center')
                ax_cat_pie.axis('off')
            
            # 4. Monthly Spending - Bar Chart
            ax_monthly = fig.add_subplot(gs[1, 3:])
            
            if months:
                # Sort months by calendar order
                month_order = ["january", "february", "march", "april", "may", "june", 
                            "july", "august", "september", "october", "november", "december"]
                # Filter to only include months that are in our data
                sorted_months = [m for m in month_order if m in months]
                month_amounts = [months[m] for m in sorted_months]
                
                # Create bar chart
                bars = ax_monthly.bar(sorted_months, month_amounts, color='skyblue')
                ax_monthly.set_title('Monthly Spending')
                ax_monthly.set_xlabel('Month')
                ax_monthly.set_ylabel('Amount ($)')
                ax_monthly.tick_params(axis='x', rotation=45)
                
                # Format y-axis as currency
                ax_monthly.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x:.0f}'))
                
                # Add amount labels to bars
                for bar in bars:
                    height = bar.get_height()
                    ax_monthly.annotate(f'${height:.0f}',
                                    xy=(bar.get_x() + bar.get_width() / 2, height),
                                    xytext=(0, 3),
                                    textcoords="offset points",
                                    ha='center', va='bottom',
                                    rotation=45)
            else:
                ax_monthly.text(0.5, 0.5, "No monthly data available", ha='center', va='center')
                ax_monthly.axis('off')
            
            # 5. Amount Distribution - Histogram
            ax_hist = fig.add_subplot(gs[2, :3])
            
            amounts = [expense[2] for expense in expenses]
            
            # Create histogram with appropriate bins
            bins = min(20, len(set(amounts)))
            ax_hist.hist(amounts, bins=bins, alpha=0.7, color='lightgreen', edgecolor='black')
            ax_hist.set_title('Amount Distribution')
            ax_hist.set_xlabel('Amount ($)')
            ax_hist.set_ylabel('Frequency')
            
            # Add a vertical line for the average
            ax_hist.axvline(avg_amount, color='red', linestyle='dashed', linewidth=1)
            ax_hist.text(
                avg_amount, 
                ax_hist.get_ylim()[1] * 0.9, 
                f'Avg: ${avg_amount:.2f}', 
                color='red',
                ha='center', 
                va='center',
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none')
            )
            
            # 6. Payment Method Distribution
            ax_payment = fig.add_subplot(gs[2, 3:])
            
            if payment_methods:
                # Sort payment methods by count
                sorted_methods = sorted(payment_methods.items(), key=lambda x: x[1]["count"], reverse=True)
                
                method_names = [method[0] for method in sorted_methods]
                method_counts = [method[1]["count"] for method in sorted_methods]
                
                # Create horizontal bar chart with colorful bars
                colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(method_names)))
                bars = ax_payment.barh(method_names, method_counts, color=colors)
                
                ax_payment.set_title('Payment Method Usage')
                ax_payment.set_xlabel('Number of Expenses')
                
                # Add count labels to bars
                for i, bar in enumerate(bars):
                    width = bar.get_width()
                    ax_payment.text(
                        width + 0.3, 
                        bar.get_y() + bar.get_height()/2, 
                        f'{width:.0f}',
                        ha='left', 
                        va='center',
                        fontweight='bold'
                    )
            else:
                ax_payment.text(0.5, 0.5, "No payment method data available", ha='center', va='center')
                ax_payment.axis('off')
            
            plt.tight_layout()
            plt.subplots_adjust(top=0.93)  # Adjust for main title
            
            plt.show(block=False)
            plt.pause(0.001)
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating analytics dashboard: {e}")
            
    # ...rest of the methods...
    
    def get_top_expenses(self, start_date, end_date, limit=10):
        """Return top N expenses for a given date range to be displayed in UI"""
        try:
            # Validate inputs
            limit = int(limit)
            if limit <= 0:
                return []

            # Validate date format
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
            
            # Use query from sql_queries.py
            query = REPORT_QUERIES["top_expenses"]
            
            if self.privileges != "admin":
                query = query.format(user_filter="AND ue.username = ?")
                params = [start_date, end_date, self.current_user, limit]
            else:
                query = query.format(user_filter="")
                params = [start_date, end_date, limit]
            
            # Execute query
            self.cursor.execute(query, params)
            expenses = self.cursor.fetchall()
            
            return expenses
        except (sqlite3.Error, ValueError) as e:
            print(f"Error in get_top_expenses: {e}")
            return []
            
    # ...rest of the methods...
    
    def get_expenses_by_payment_method(self, payment_method):
        """Get expenses for a specific payment method as a pandas DataFrame"""
        try:
            # Validate payment method
            self.cursor.execute("SELECT payment_method_id FROM Payment_Method WHERE payment_method_name = ?", 
                              (payment_method,))
            result = self.cursor.fetchone()
            if result is None:
                return pd.DataFrame()
                
            payment_method_id = result[0]
            
            # Create query based on privileges and using the correct schema from BASE_EXPENSE_QUERY
            base_query = """
                SELECT 
                    e.expense_id, 
                    e.date, 
                    e.amount, 
                    e.description, 
                    c.category_name as category, 
                    t.tag_name as tag,
                    pm.payment_method_name as payment_method,
                    pme.payment_detail_identifier
                FROM 
                    Expense e
                    LEFT JOIN Category_Expense ce ON e.expense_id = ce.expense_id
                    LEFT JOIN Categories c ON ce.category_id = c.category_id
                    LEFT JOIN Tag_Expense te ON e.expense_id = te.expense_id
                    LEFT JOIN Tags t ON te.tag_id = t.tag_id
                    JOIN Payment_Method_Expense pme ON e.expense_id = pme.expense_id
                    JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                    JOIN User_Expense ue ON e.expense_id = ue.expense_id
                WHERE 
                    pme.payment_method_id = ?
            """
            
            if self.privileges != "admin":
                base_query += " AND ue.username = ?"
                params = (payment_method_id, self.current_user)
            else:
                params = (payment_method_id,)
            
            # Execute query and convert to DataFrame
            expenses_df = pd.read_sql_query(base_query, self.conn, params=params)
            return expenses_df
            
        except (sqlite3.Error, ValueError) as e:
            print(f"Error getting expenses by payment method: {e}")
            return pd.DataFrame()  # Return empty DataFrame on error
    
    def get_category_expenses(self, category):
        """Get expenses for a specific category as a pandas DataFrame"""
        try:
            # Check if category exists
            self.cursor.execute("SELECT category_id FROM Categories WHERE category_name = ?", (category,))
            result = self.cursor.fetchone()
            if result is None:
                return pd.DataFrame()
                
            category_id = result[0]
            
            # Create query based on privileges
            base_query = """
                SELECT 
                    e.expense_id, 
                    e.date, 
                    e.amount, 
                    e.description,
                    t.tag_name as tag
                FROM 
                    Expense e
                    JOIN Category_Expense ce ON e.expense_id = ce.expense_id 
                    LEFT JOIN Tag_Expense te ON e.expense_id = te.expense_id
                    LEFT JOIN Tags t ON te.tag_id = t.tag_id
                    JOIN User_Expense ue ON e.expense_id = ue.expense_id
                WHERE 
                    ce.category_id = ?
            """
            
            if self.privileges != "admin":
                base_query += " AND ue.username = ?"
                params = (category_id, self.current_user)
            else:
                params = (category_id,)
            
            # Order by date descending
            base_query += " ORDER BY e.date DESC"
            
            # Execute query and convert to DataFrame
            expenses_df = pd.read_sql_query(base_query, self.conn, params=params)
            return expenses_df
            
        except (sqlite3.Error, ValueError) as e:
            print(f"Error getting category expenses: {e}")
            return pd.DataFrame()  # Return empty DataFrame on error
    
    # ...existing code...
    
    def get_above_average_expenses(self):
        """Get expenses that are above average for their respective categories
        
        Returns:
            pandas.DataFrame: DataFrame containing expenses above their category average
        """
        try:
            # First, get category averages
            if self.privileges != "admin":
                category_avg_query = """
                    SELECT 
                        c.category_name, 
                        AVG(e.amount) as avg_amount
                    FROM 
                        Expense e
                        JOIN Category_Expense ce ON e.expense_id = ce.expense_id
                        JOIN Categories c ON ce.category_id = c.category_id
                        JOIN User_Expense ue ON e.expense_id = ue.expense_id
                    WHERE 
                        ue.username = ?
                    GROUP BY 
                        c.category_name
                """
                self.cursor.execute(category_avg_query, (self.current_user,))
            else:
                category_avg_query = """
                    SELECT 
                        c.category_name, 
                        AVG(e.amount) as avg_amount
                    FROM 
                        Expense e
                        JOIN Category_Expense ce ON e.expense_id = ce.expense_id
                        JOIN Categories c ON ce.category_id = c.category_id
                    GROUP BY 
                        c.category_name
                """
                self.cursor.execute(category_avg_query)
                
            # Store category averages
            category_avgs = {row[0]: row[1] for row in self.cursor.fetchall()}
            
            if not category_avgs:
                return pd.DataFrame()  # No categories found
            
            # Now get all expenses with their categories
            if self.privileges != "admin":
                expense_query = """
                    SELECT 
                        e.expense_id,
                        e.date,
                        e.amount,
                        e.description,
                        c.category_name
                    FROM 
                        Expense e
                        JOIN Category_Expense ce ON e.expense_id = ce.expense_id
                        JOIN Categories c ON ce.category_id = c.category_id
                        JOIN User_Expense ue ON e.expense_id = ue.expense_id
                    WHERE 
                        ue.username = ?
                    ORDER BY 
                        e.amount DESC
                """
                self.cursor.execute(expense_query, (self.current_user,))
            else:
                expense_query = """
                    SELECT 
                        e.expense_id,
                        e.date,
                        e.amount,
                        e.description,
                        c.category_name
                    FROM 
                        Expense e
                        JOIN Category_Expense ce ON e.expense_id = ce.expense_id
                        JOIN Categories c ON ce.category_id = c.category_id
                    ORDER BY 
                        e.amount DESC
                """
                self.cursor.execute(expense_query)
            
            expenses = []
            for row in self.cursor.fetchall():
                expense_id, date, amount, description, category = row
                
                # Skip if category doesn't have average (shouldn't happen but just in case)
                if category not in category_avgs:
                    continue
                    
                category_avg = category_avgs[category]
                
                # Only include expenses above their category average
                if amount > category_avg:
                    # Calculate percent above average
                    percent_above = ((amount - category_avg) / category_avg) * 100
                    
                    expenses.append({
                        "ID": expense_id,
                        "Date": date,
                        "Amount": amount,
                        "Description": description,
                        "Category": category,
                        "Category Avg": category_avg,
                        "Percent Above Avg": percent_above
                    })
            
            if not expenses:
                return pd.DataFrame()  # No above-average expenses found
                
            # Convert to DataFrame and sort by percent above average
            df = pd.DataFrame(expenses)
            df = df.sort_values(by="Percent Above Avg", ascending=False)
            
            return df
            
        except (sqlite3.Error, ValueError) as e:
            print(f"Error getting above average expenses: {e}")
            return pd.DataFrame()  # Return empty DataFrame on error
    
    # ...existing code...