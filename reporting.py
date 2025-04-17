import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import os
from sql_queries import REPORT_QUERIES

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

    def generate_report_payment_method_details_expense(self):
        """Report on expenses with payment method details - analyzing frequency, total, and average amounts"""
        try:
            # Use query from sql_queries.py
            self.cursor.execute(REPORT_QUERIES["payment_method_details"], (self.current_user,))
            results = self.cursor.fetchall()
            
            if not results:
                print("No expenses with payment method details found.")
                return
                
            # Display results
            print("\nPayment Method Details Usage Report:")
            print("-" * 80)
            print(f"{'Payment Detail':<20} {'Usage Count':<12} {'Total Amount':<15} {'Avg Amount':<15} {'Payment Method':<20}")
            print("-" * 80)
            
            total_transactions = 0
            total_amount = 0
            
            for row in results:
                detail, count, total, avg, method = row
                total_transactions += count
                total_amount += total
                
                # Mask sensitive payment details for privacy
                if method[-4:] == "card":
                    masked_detail = self._mask_payment_details(detail)
                else:
                    masked_detail = detail
                
                print(f"{masked_detail:<20} {count:<12} {total:<15.2f} {avg:<15.2f} {method:<20}")
            
            print("-" * 80)
            print(f"Overall Total: {total_transactions} transactions, ${total_amount:.2f}")
            print(f"Overall Average: ${total_amount/total_transactions:.2f} per transaction")
            
            # Create visualizations if we have data
            if results:
                import matplotlib.pyplot as plt
                import numpy as np
                from matplotlib.ticker import FuncFormatter
                
                # Prepare data for plotting
                details = [self._mask_payment_details(r[0]) if r[4][-4:] == "card" else r[0] for r in results]
                counts = [r[1] for r in results]
                totals = [r[2] for r in results]
                avgs = [r[3] for r in results]
                methods = [r[4] for r in results]
                
                # If too many details, limit to top 10 for readability
                if len(details) > 10:
                    details = details[:10]
                    counts = counts[:10]
                    totals = totals[:10]
                    avgs = avgs[:10]
                    methods = methods[:10]
                
                # Create figure with 3 subplots (removed 4th plot)
                fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 6))
                
                # 1. Bar chart showing frequency of usage
                bars1 = ax1.bar(details, counts, color='skyblue')
                ax1.set_title('Frequency of Usage')
                ax1.set_xlabel('Payment Detail (masked)')
                ax1.set_ylabel('Number of Transactions')
                ax1.tick_params(axis='x', rotation=45)
                
                # Add count labels with slanted text
                for bar in bars1:
                    height = bar.get_height()
                    ax1.annotate(f'{height}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom',
                                rotation=45)
                
                # 2. Bar chart showing total amount spent
                bars2 = ax2.bar(details, totals, color='lightgreen')
                ax2.set_title('Total Amount Spent')
                ax2.set_xlabel('Payment Detail (masked)')
                ax2.set_ylabel('Total Amount ($)')
                ax2.tick_params(axis='x', rotation=45)
                
                # Format y-axis as currency
                ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x:.0f}'))
                
                # Add amount labels with slanted text
                for bar in bars2:
                    height = bar.get_height()
                    ax2.annotate(f'${height:.2f}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom',
                                rotation=45)
                
                # 3. Bar chart showing average transaction amount
                bars3 = ax3.bar(details, avgs, color='salmon')
                ax3.set_title('Average Transaction Amount')
                ax3.set_xlabel('Payment Detail (masked)')
                ax3.set_ylabel('Average Amount ($)')
                ax3.tick_params(axis='x', rotation=45)
                
                # Format y-axis as currency
                ax3.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x:.0f}'))
                
                # Add amount labels with slanted text
                for bar in bars3:
                    height = bar.get_height()
                    ax3.annotate(f'${height:.2f}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom',
                                rotation=45)
                
                plt.tight_layout()
                plt.suptitle('Payment Method Details Analysis', fontsize=16, y=1.05)
                
                plt.show(block=False)
                plt.pause(0.001)
                
        except Exception as e:
            print(f"Error generating report: {e}")

    def generate_report_payment_method_usage(self):
        """Report spending breakdown by payment method"""
        try:
            # Use query from sql_queries.py
            query = REPORT_QUERIES["payment_method_usage"]
            if self.privileges != "admin":
                query = query.format(user_filter="WHERE ue.username = ?")
                params = [self.current_user]
            else:
                query = query.format(user_filter="")
                params = []
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            if not results:
                print("No payment method usage data available.")
                return
                
            # Display results
            print("\nPayment Method Usage Report:")
            print("-" * 60)
            print(f"{'Payment Method':<20} {'Usage Count':<15} {'Total Amount':<15} {'Avg Amount':<15}")
            print("-" * 60)
            
            for method, count, total in results:
                avg_amount = total / count
                print(f"{method:<20} {count:<15} {total:<15.2f} {avg_amount:<15.2f}")
                
            print("-" * 60)
            
            # Create a pie chart
            if results:
                plt.figure(figsize=(10, 8))
                
                # Extract data for plotting
                methods = [result[0] for result in results]
                amounts = [result[2] for result in results]
                
                # Create pie chart
                plt.pie(amounts, labels=methods, autopct='%1.1f%%', startangle=90, shadow=True)
                plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                plt.title('Spending by Payment Method')
                plt.tight_layout()
                
                plt.show(block=False)
                plt.pause(0.001)
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")
    
    def generate_report_frequent_category(self):
        """Report the most frequently used expense category"""
        try:
            # Use query from sql_queries.py
            query = REPORT_QUERIES["frequent_category"]
            if self.privileges != "admin":
                query = query.format(user_filter="WHERE ue.username = ?")
                params = [self.current_user]
            else:
                query = query.format(user_filter="")
                params = []
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            if not results:
                print("No expenses found to generate frequent category report.")
                return
                
            # Display results
            print("\nCategory Usage Report:")
            print("-" * 60)
            print(f"{'Category':<20} {'Usage Count':<15} {'Total Amount':<15} {'Avg Amount':<15}")
            print("-" * 60)
            
            for category, count, total in results:
                avg_amount = total / count
                print(f"{category:<20} {count:<15} {total:<15.2f} {avg_amount:<15.2f}")
                
            print("-" * 60)
            print(f"Most frequently used category: {results[0][0]} ({results[0][1]} uses)")
            
            # Create a horizontal bar chart
            if len(results) > 0:
                plt.figure(figsize=(10, max(6, len(results) * 0.4)))
                
                # Extract data for plotting
                categories = [result[0] for result in results]
                counts = [result[1] for result in results]
                
                # Sort data for better visualization
                categories.reverse()
                counts.reverse()
                
                # Create horizontal bar chart
                bars = plt.barh(categories, counts, color='purple')
                
                # Add count labels
                for i, v in enumerate(counts):
                    plt.text(v + 0.5, i, str(v), va='center')
                
                plt.xlabel('Usage Count')
                plt.title('Category Usage Frequency')
                plt.tight_layout()
                
                plt.show(block=False)
                plt.pause(0.001)
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")

    def generate_report_highest_spender_per_month(self):
        """Report the user with highest spending for each month (admin only)"""
        if self.privileges != "admin":
            print("Error: This report is only available for administrators.")
            return
            
        try:
            # Use query from sql_queries.py
            self.cursor.execute(REPORT_QUERIES["highest_spender_per_month"])
            results = self.cursor.fetchall()
            
            if not results:
                print("No data available to generate highest spender report.")
                return
                
            # Display results in table format
            print("\nHighest Spender per Month:")
            print("-" * 50)
            print(f"{'Month':<15} {'Username':<20} {'Total Spending':<15}")
            print("-" * 50)
            
            for month, username, total in results:
                print(f"{month:<15} {username:<20} {total:<15.2f}")
                
            print("-" * 50)
            
            # Create enhanced visualization
            plt.figure(figsize=(14, 8))
            
            # Extract data for plotting
            months = [result[0] for result in results]
            amounts = [result[2] for result in results]
            usernames = [result[1] for result in results]
            
            # Create a custom colormap with gradient for visual appeal
            unique_users = list(set(usernames))
            cmap = plt.cm.viridis
            colors = cmap(np.linspace(0.1, 0.9, len(unique_users)))
            user_colors = {user: colors[i] for i, user in enumerate(unique_users)}
            
            # Plot the bars with enhanced styling
            bars = plt.bar(
                months, 
                amounts, 
                color=[user_colors[user] for user in usernames],
                width=0.6,
                edgecolor='white',
                linewidth=1.5,
                alpha=0.8
            )
            
            # Add annotations for each bar
            for bar, username, amount in zip(bars, usernames, amounts):
                # Username at the top of the bar
                plt.text(
                    bar.get_x() + bar.get_width()/2, 
                    bar.get_height() + (max(amounts) * 0.03), 
                    username,
                    ha='center',
                    fontsize=10,
                    fontweight='bold'
                )
                
                # Amount inside the bar
                plt.text(
                    bar.get_x() + bar.get_width()/2,
                    bar.get_height()/2,
                    f'${amount:.2f}',
                    ha='center',
                    va='center',
                    fontsize=9,
                    fontweight='bold',
                    color='white'
                )
            
            # Enhance the plot styling
            plt.xlabel('Month', fontsize=12, fontweight='bold')
            plt.ylabel('Total Spending ($)', fontsize=12, fontweight='bold')
            plt.title('Highest Spender Per Month', fontsize=16, fontweight='bold', pad=20)
            
            # Add a subtle grid for easier reading
            plt.grid(axis='y', linestyle='--', alpha=0.3)
            
            # Style the axis
            plt.xticks(rotation=45, fontsize=10)
            plt.yticks(fontsize=10)
            
            # Create legend for users
            from matplotlib.patches import Patch
            legend_elements = [Patch(facecolor=user_colors[user], label=user, edgecolor='white', linewidth=1) 
                              for user in unique_users]
            plt.legend(
                handles=legend_elements, 
                title="Users", 
                title_fontsize=12,
                loc='upper right',
                frameon=True,
                framealpha=0.95,
                edgecolor='lightgray'
            )
            
            # Add a note about the data
            plt.figtext(
                0.5, 0.01, 
                "Note: Shows only the top spender for each month", 
                ha='center', fontsize=9, fontstyle='italic'
            )
            
            plt.tight_layout()
            plt.show(block=False)
            plt.pause(0.001)
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")
    
    def generate_report_monthly_category_spending(self):
        """Report total spending per category for each month"""
        try:
            # Use query from sql_queries.py
            query = REPORT_QUERIES["monthly_category_spending"]
            if self.privileges != "admin":
                query = query.format(user_filter="WHERE ue.username = ?")
                params = [self.current_user]
            else:
                query = query.format(user_filter="")
                params = []
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            if not results:
                print("No expenses found to generate monthly category spending report.")
                return
                
            # Organize data by month
            months = {}
            for month, category, total, count in results:
                if month not in months:
                    months[month] = []
                months[month].append((category, total, count))
                
            # Display results
            print("\nMonthly Category Spending Report:")
            
            for month in sorted(months.keys()):
                print(f"\n{month} Breakdown:")
                print("-" * 60)
                print(f"{'Category':<20} {'Amount':<15} {'Count':<10} {'Avg per Expense':<15}")
                print("-" * 60)
                
                month_total = 0
                for category, total, count in months[month]:
                    avg_per_expense = total / count
                    month_total += total
                    print(f"{category:<20} {total:<15.2f} {count:<10} {avg_per_expense:<15.2f}")
                    
                print("-" * 60)
                print(f"Month Total: {month_total:.2f}")
                
            # Create a stacked bar chart
            plt.figure(figsize=(14, 8))
            
            # Get unique months and categories
            all_months = sorted(months.keys())
            all_categories = sorted(set(category for month_data in months.values() 
                                   for category, _, _ in month_data))
            
            # Create data structure for plotting
            data = {}
            for category in all_categories:
                data[category] = []
                for month in all_months:
                    amount = next((total for cat, total, _ in months[month] if cat == category), 0)
                    data[category].append(amount)
            
            # Create the stacked bar chart
            bottom = np.zeros(len(all_months))
            for category in all_categories:
                plt.bar(all_months, data[category], bottom=bottom, label=category)
                bottom += np.array(data[category])
            
            plt.xlabel('Month')
            plt.ylabel('Amount')
            plt.title('Monthly Spending by Category')
            plt.legend(title='Categories', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            plt.show(block=False)
            plt.pause(0.001)
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")
    
    
    def generate_report_above_average_expenses(self):
        """Report expenses that are above the category average, grouped by category"""
        try:
            # Use query from sql_queries.py
            if self.privileges != "admin":
                user_filter_subquery = "WHERE ue.username = ?"
                user_filter = "AND ue.username = ?"
                params = [self.current_user, self.current_user]
            else:
                user_filter_subquery = ""
                user_filter = ""
                params = []
            
            query = REPORT_QUERIES["above_average_expenses"].format(
                user_filter_subquery=user_filter_subquery,
                user_filter=user_filter
            )
            
            self.cursor.execute(query, params)
            expenses = self.cursor.fetchall()
            
            if not expenses:
                print("No above-average expenses found.")
                return
            
            # Organize results by category
            category_expenses = {}
            
            for expense in expenses:
                expense_id, date, amount, description, category, avg_amount, tag, payment_method, username = expense
                # Calculate percentage difference
                percentage_diff = ((amount - avg_amount) / avg_amount) * 100
                
                # Add percentage diff to the expense data
                expense_with_diff = expense + (percentage_diff,)
                
                if category not in category_expenses:
                    category_expenses[category] = []
                category_expenses[category].append(expense_with_diff)
            
            # Sort each category's expenses by percentage diff (descending)
            for category in category_expenses:
                category_expenses[category].sort(key=lambda x: x[9], reverse=True)
            
            # Display results by category
            print("\nExpenses Above Category Average (By Category):")
            
            # Get total count for summary
            total_above_avg = 0
            
            # Display a table for each category
            for category in sorted(category_expenses.keys()):
                cat_expenses = category_expenses[category]
                total_above_avg += len(cat_expenses)
                
                print(f"\n{category.upper()} CATEGORY:")
                print("-" * 110)
                
                # Different headers based on user role
                if self.privileges == "admin":
                    print(f"{'ID':<5} {'Date':<12} {'Amount':<10} {'Avg Amount':<12} {'Diff %':<10} {'Username':<12} {'Description':<25}")
                    print("-" * 110)
                    
                    for expense in cat_expenses:
                        expense_id, date, amount, description, _, avg_amount, _, _, username, percentage_diff = expense
                        description = (description[:22] + "...") if description and len(description) > 25 else (description or "")
                        
                        print(f"{expense_id:<5} {date:<12} {amount:<10.2f} {avg_amount:<12.2f} {percentage_diff:>+10.2f}% {username:<12} {description:<25}")
                else:
                    print(f"{'ID':<5} {'Date':<12} {'Amount':<10} {'Avg Amount':<12} {'Diff %':<10} {'Payment Method':<15} {'Description':<25}")
                    print("-" * 110)
                    
                    for expense in cat_expenses:
                        expense_id, date, amount, description, _, avg_amount, _, payment_method, _, percentage_diff = expense
                        description = (description[:22] + "...") if description and len(description) > 25 else (description or "")
                        
                        print(f"{expense_id:<5} {date:<12} {amount:<10.2f} {avg_amount:<12.2f} {percentage_diff:>+10.2f}% {payment_method:<15} {description:<25}")
                
                print("-" * 110)
                print(f"Category total: {len(cat_expenses)} expense(s) above average")
            
            # Display overall summary
            print("\nSUMMARY:")
            print("-" * 60)
            print(f"Total: {total_above_avg} expense(s) above their category average")
            print(f"Categories with above-average expenses: {len(category_expenses)}")
            
            # Create visualization showing expenses by category
            if category_expenses:
                plt.figure(figsize=(14, 10))
                
                # Create a scatter plot with categories on x-axis
                all_categories = list(category_expenses.keys())
                category_indices = {cat: i for i, cat in enumerate(all_categories)}
                
                # Plot points for each expense
                x_values = []
                y_values = []
                sizes = []
                colors = []
                annotations = []
                
                # Color map for percentage differences
                cmap = plt.cm.get_cmap('RdYlGn_r')
                
                for cat, expenses in category_expenses.items():
                    cat_idx = category_indices[cat]
                    for exp in expenses:
                        amount = exp[2]
                        avg = exp[5]
                        diff_pct = exp[9]
                        
                        # Add jitter to x position to avoid overlapping points
                        jitter = (np.random.random() - 0.5) * 0.3
                        x_values.append(cat_idx + jitter)
                        y_values.append(amount)
                        
                        # Size based on amount
                        sizes.append(50 + (amount/max(exp[2] for exp in expenses)) * 100)
                        
                        # Color based on percentage difference (normalize to 0-1 range)
                        norm_diff = min(1.0, diff_pct / 200)  # Cap at 200% difference
                        colors.append(cmap(norm_diff))
                        
                        # Annotation with expense ID and diff%
                        annotations.append(f"ID:{exp[0]}\n+{diff_pct:.1f}%")
                
                # Draw scatter plot
                scatter = plt.scatter(x_values, y_values, s=sizes, c=colors, alpha=0.7)
                
                # Draw category average lines
                for cat, expenses in category_expenses.items():
                    cat_idx = category_indices[cat]
                    avg = expenses[0][5]  # All expenses in a category have the same average
                    plt.hlines(avg, cat_idx - 0.4, cat_idx + 0.4, colors='blue', linestyles='dashed', 
                               label='Category Average' if cat == list(category_expenses.keys())[0] else "")
                
                # Add hover annotations
                from matplotlib.offsetbox import OffsetImage, AnnotationBbox
                
                # Label axes and title
                plt.xlabel('Category')
                plt.ylabel('Amount')
                plt.title('Above-Average Expenses by Category')
                plt.xticks(range(len(all_categories)), all_categories)
                plt.grid(True, linestyle='--', alpha=0.3)
                
                # Add legend
                plt.colorbar(scatter, label='Percentage Above Average')
                plt.legend()
                
                # Display the plot
                plt.tight_layout()
                plt.show()
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")

    def generate_report_tag_expenses(self):
        """Report number of expenses for each tag"""
        try:
            # Use query from sql_queries.py
            query = REPORT_QUERIES["tag_expenses"]
            if self.privileges != "admin":
                query = query.format(user_filter="WHERE ue.username = ?")
                params = [self.current_user]
            else:
                query = query.format(user_filter="")
                params = []
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            
            if not results:
                print("No tag usage data available.")
                return
                
            # Display results
            print("\nTag Usage Report:")
            print("-" * 60)
            print(f"{'Tag':<20} {'Usage Count':<15} {'Total Amount':<15} {'Avg Amount':<15}")
            print("-" * 60)
            
            for tag, count, total in results:
                avg_amount = total / count
                print(f"{tag:<20} {count:<15} {total:<15.2f} {avg_amount:<15.2f}")
                
            print("-" * 60)
            
            # Create a horizontal bar chart for counts
            if results:
                # Create figure with single plot
                plt.figure(figsize=(10, 8))
                
                # Extract data for plotting
                tags = [result[0] for result in results]
                counts = [result[1] for result in results]
                amounts = [result[2] for result in results]
                
                # Sort data by count for better visualization
                sorted_data = sorted(zip(tags, counts, amounts), key=lambda x: x[1])
                tags = [x[0] for x in sorted_data]
                counts = [x[1] for x in sorted_data]
                
                # Bar chart for usage count
                plt.barh(tags, counts, color='teal')
                plt.xlabel('Usage Count')
                plt.title('Tag Usage Frequency')
                
                # Add count labels
                for i, v in enumerate(counts):
                    plt.text(v + 0.1, i, str(v), va='center')
                
                plt.tight_layout()
                plt.show(block=False)
                plt.pause(0.001)
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error generating report: {e}")
            
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