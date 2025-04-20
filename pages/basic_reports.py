import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from reporting import ReportManager
from logs import LogManager

def show_basic_reports():
    st.markdown("<div class='main-header'>Basic Reports</div>", unsafe_allow_html=True)
    
    # Get database connection and managers
    conn = sqlite3.connect("ExpenseReport", check_same_thread=False)
    cursor = conn.cursor()
    report_manager = ReportManager(cursor, conn)
    report_manager.set_user_info(st.session_state.username, st.session_state.role)
    log_manager = LogManager(cursor, conn)
    log_manager.set_current_user(st.session_state.username)
    
    # Create tabs for different report types
    tabs = ["Top Expenses", "Category Spending", "Monthly Category Spending", 
            "Payment Method Usage", "Frequent Category", "Tag Expenses"]
    
    # Add admin-only reports
    if st.session_state.role == "admin":
        tabs.append("Highest Spender Per Month")
    
    selected_tab = st.selectbox("Select Report Type", tabs)
    
    # Report: Top Expenses
    if selected_tab == "Top Expenses":
        st.subheader("Top Expenses Report")
        
        # Input parameters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            top_n = st.number_input("Number of expenses to show", min_value=1, max_value=50, value=10)
        
        with col2:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=90))
        
        with col3:
            end_date = st.date_input("End Date", value=datetime.now())
        
        if start_date > end_date:
            st.error("Start date must be before end date.")
            return
        
        # Convert dates to string format
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        if st.button("Generate Top Expenses Report"):
            # Build the query
            if st.session_state.role == "admin":
                query = f"""
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
                    WHERE e.date BETWEEN ? AND ?
                    ORDER BY e.amount DESC
                    LIMIT {top_n}
                """
                params = [start_date_str, end_date_str]
            else:
                query = f"""
                    SELECT e.expense_id, e.date, e.amount, e.description, 
                        c.category_name, t.tag_name, pm.payment_method_name
                    FROM Expense e
                    LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                    LEFT JOIN Categories c ON ce.category_id = c.category_id
                    LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
                    LEFT JOIN Tags t ON te.tag_id = t.tag_id
                    LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
                    LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                    LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
                    WHERE e.date BETWEEN ? AND ?
                    AND ue.username = ?
                    ORDER BY e.amount DESC
                    LIMIT {top_n}
                """
                params = [start_date_str, end_date_str, st.session_state.username]
            
            cursor.execute(query, params)
            expenses = cursor.fetchall()
            
            if expenses:
                if st.session_state.role == "admin":
                    columns = ["ID", "Date", "Amount", "Description", "Category", "Tag", "Payment Method", "User"]
                else:
                    columns = ["ID", "Date", "Amount", "Description", "Category", "Tag", "Payment Method"]
                
                df = pd.DataFrame(expenses, columns=columns)
                
                # Display as table
                st.dataframe(df, use_container_width=True)
                
                # Create bar chart of top expenses
                fig = px.bar(
                    df, 
                    x='Amount', 
                    y=df.index, 
                    orientation='h',
                    text='Amount',
                    color='Category',
                    hover_data=['Date', 'Description'],
                    title=f'Top {top_n} Expenses ({start_date_str} to {end_date_str})',
                    labels={'y': 'Expense ID'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                log_manager.add_log(log_manager.generate_log_description("report", ["top_expenses", str(top_n), start_date_str, end_date_str]))
            else:
                st.info("No expenses found for the selected date range.")
    
    # Report: Category Spending
    elif selected_tab == "Category Spending":
        st.subheader("Category Spending Report")
        
        # Get available categories
        cursor.execute("SELECT category_name FROM Categories")
        categories = [cat[0] for cat in cursor.fetchall()]
        
        if not categories:
            st.warning("No categories found in the system.")
        else:
            selected_category = st.selectbox("Select Category", categories)
            
            if st.button("Generate Category Spending Report"):
                # Build the query
                if st.session_state.role == "admin":
                    query = """
                        SELECT e.date, e.amount, e.description
                        FROM Expense e
                        LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                        LEFT JOIN Categories c ON ce.category_id = c.category_id
                        WHERE c.category_name = ?
                        ORDER BY e.date DESC
                    """
                    params = [selected_category]
                else:
                    query = """
                        SELECT e.date, e.amount, e.description
                        FROM Expense e
                        LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                        LEFT JOIN Categories c ON ce.category_id = c.category_id
                        LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
                        WHERE c.category_name = ? AND ue.username = ?
                        ORDER BY e.date DESC
                    """
                    params = [selected_category, st.session_state.username]
                
                cursor.execute(query, params)
                expenses = cursor.fetchall()
                
                if expenses:
                    df = pd.DataFrame(expenses, columns=["Date", "Amount", "Description"])
                    df['Date'] = pd.to_datetime(df['Date'])
                    
                    # Summary statistics
                    total_amount = df['Amount'].sum()
                    average_amount = df['Amount'].mean()
                    max_amount = df['Amount'].max()
                    count = len(df)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total", f"${total_amount:.2f}")
                    col2.metric("Average", f"${average_amount:.2f}")
                    col3.metric("Maximum", f"${max_amount:.2f}")
                    col4.metric("Count", count)
                    
                    # Display as table
                    st.dataframe(df, use_container_width=True)
                    
                    # Create time series chart
                    # Group by month
                    df['month'] = df['Date'].dt.to_period('M').astype(str)
                    monthly_data = df.groupby('month')['Amount'].sum().reset_index()
                    
                    fig = px.line(
                        monthly_data, 
                        x='month', 
                        y='Amount',
                        title=f'Monthly Spending for {selected_category}',
                        markers=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    log_manager.add_log(log_manager.generate_log_description("report", ["category_spending", selected_category]))
                else:
                    st.info(f"No expenses found for category '{selected_category}'.")
    
    # Report: Monthly Category Spending
    elif selected_tab == "Monthly Category Spending":
        st.subheader("Monthly Category Spending")
        
        year = st.selectbox("Select Year", list(range(datetime.now().year, datetime.now().year - 10, -1)))
        
        if st.button("Generate Monthly Category Spending Report"):
            # Build the query
            if st.session_state.role == "admin":
                query = """
                    SELECT 
                        strftime('%m', e.date) as month,
                        c.category_name,
                        SUM(e.amount) as total_amount
                    FROM Expense e
                    LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                    LEFT JOIN Categories c ON ce.category_id = c.category_id
                    WHERE strftime('%Y', e.date) = ?
                    GROUP BY strftime('%m', e.date), c.category_name
                    ORDER BY month, c.category_name
                """
                params = [str(year)]
            else:
                query = """
                    SELECT 
                        strftime('%m', e.date) as month,
                        c.category_name,
                        SUM(e.amount) as total_amount
                    FROM Expense e
                    LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                    LEFT JOIN Categories c ON ce.category_id = c.category_id
                    LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
                    WHERE strftime('%Y', e.date) = ? AND ue.username = ?
                    GROUP BY strftime('%m', e.date), c.category_name
                    ORDER BY month, c.category_name
                """
                params = [str(year), st.session_state.username]
            
            cursor.execute(query, params)
            data = cursor.fetchall()
            
            if data:
                df = pd.DataFrame(data, columns=["Month", "Category", "Amount"])
                
                # Convert month number to month name
                month_map = {
                    '01': 'January', '02': 'February', '03': 'March', '04': 'April',
                    '05': 'May', '06': 'June', '07': 'July', '08': 'August',
                    '09': 'September', '10': 'October', '11': 'November', '12': 'December'
                }
                df['Month'] = df['Month'].map(month_map)
                
                # Create pivot table for better visualization
                pivot_df = df.pivot(index="Month", columns="Category", values="Amount").fillna(0)
                
                # Ensure months are in correct order
                month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                            'July', 'August', 'September', 'October', 'November', 'December']
                pivot_df = pivot_df.reindex(month_order)
                
                # Display as table
                st.write(f"### Category Spending by Month ({year})")
                st.dataframe(pivot_df, use_container_width=True)
                
                # Create stacked bar chart
                fig = go.Figure()
                
                for category in pivot_df.columns:
                    fig.add_trace(go.Bar(
                        x=pivot_df.index,
                        y=pivot_df[category],
                        name=category
                    ))
                
                fig.update_layout(
                    title=f'Monthly Category Spending ({year})',
                    xaxis_title='Month',
                    yaxis_title='Amount',
                    barmode='stack'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                log_manager.add_log(log_manager.generate_log_description("report", ["monthly_category_spending", str(year)]))
            else:
                st.info(f"No expenses found for year {year}.")
    
    # Report: Payment Method Usage
    elif selected_tab == "Payment Method Usage":
        st.subheader("Payment Method Usage Report")
        
        if st.button("Generate Payment Method Usage Report"):
            # Build the query
            if st.session_state.role == "admin":
                query = """
                    SELECT 
                        pm.payment_method_name,
                        COUNT(e.expense_id) as usage_count,
                        SUM(e.amount) as total_amount
                    FROM Expense e
                    LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
                    LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                    GROUP BY pm.payment_method_name
                    ORDER BY total_amount DESC
                """
                params = []
            else:
                query = """
                    SELECT 
                        pm.payment_method_name,
                        COUNT(e.expense_id) as usage_count,
                        SUM(e.amount) as total_amount
                    FROM Expense e
                    LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
                    LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                    LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
                    WHERE ue.username = ?
                    GROUP BY pm.payment_method_name
                    ORDER BY total_amount DESC
                """
                params = [st.session_state.username]
            
            cursor.execute(query, params)
            data = cursor.fetchall()
            
            if data:
                df = pd.DataFrame(data, columns=["Payment Method", "Usage Count", "Total Amount"])
                
                # Display as table
                st.dataframe(df, use_container_width=True)
                
                # Create pie chart
                fig1 = px.pie(
                    df, 
                    values='Total Amount', 
                    names='Payment Method',
                    title='Payment Method Distribution by Amount'
                )
                st.plotly_chart(fig1, use_container_width=True)
                
                # Create bar chart for usage count
                fig2 = px.bar(
                    df,
                    x='Payment Method',
                    y='Usage Count',
                    title='Payment Method Usage Frequency',
                    color='Payment Method'
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                log_manager.add_log(log_manager.generate_log_description("report", ["payment_method_usage"]))
            else:
                st.info("No payment method usage data found.")
    
    # Report: Frequent Category
    elif selected_tab == "Frequent Category":
        st.subheader("Frequent Category Report")
        
        if st.button("Generate Frequent Category Report"):
            # Build the query
            if st.session_state.role == "admin":
                query = """
                    SELECT 
                        c.category_name,
                        COUNT(e.expense_id) as usage_count,
                        SUM(e.amount) as total_amount,
                        AVG(e.amount) as average_amount
                    FROM Expense e
                    LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                    LEFT JOIN Categories c ON ce.category_id = c.category_id
                    GROUP BY c.category_name
                    ORDER BY usage_count DESC
                """
                params = []
            else:
                query = """
                    SELECT 
                        c.category_name,
                        COUNT(e.expense_id) as usage_count,
                        SUM(e.amount) as total_amount,
                        AVG(e.amount) as average_amount
                    FROM Expense e
                    LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                    LEFT JOIN Categories c ON ce.category_id = c.category_id
                    LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
                    WHERE ue.username = ?
                    GROUP BY c.category_name
                    ORDER BY usage_count DESC
                """
                params = [st.session_state.username]
            
            cursor.execute(query, params)
            data = cursor.fetchall()
            
            if data:
                df = pd.DataFrame(data, columns=["Category", "Usage Count", "Total Amount", "Average Amount"])
                df["Average Amount"] = df["Average Amount"].round(2)
                
                # Display as table
                st.dataframe(df, use_container_width=True)
                
                # Create horizontal bar chart for frequency
                fig = px.bar(
                    df,
                    y='Category',
                    x='Usage Count',
                    orientation='h',
                    title='Category Frequency',
                    text='Usage Count',
                    color='Category'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Create scatter plot of frequency vs average amount
                fig2 = px.scatter(
                    df,
                    x='Average Amount',
                    y='Usage Count',
                    size='Total Amount',
                    color='Category',
                    title='Category Frequency vs. Average Amount',
                    hover_name='Category',
                    log_x=True
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                log_manager.add_log(log_manager.generate_log_description("report", ["frequent_category"]))
            else:
                st.info("No category usage data found.")
    
    # Report: Tag Expenses
    elif selected_tab == "Tag Expenses":
        st.subheader("Expense Tags Report")
        
        if st.button("Generate Tag Expenses Report"):
            # Build the query
            if st.session_state.role == "admin":
                query = """
                    SELECT 
                        t.tag_name,
                        COUNT(e.expense_id) as usage_count,
                        SUM(e.amount) as total_amount,
                        AVG(e.amount) as average_amount
                    FROM Expense e
                    LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
                    LEFT JOIN Tags t ON te.tag_id = t.tag_id
                    GROUP BY t.tag_name
                    ORDER BY total_amount DESC
                """
                params = []
            else:
                query = """
                    SELECT 
                        t.tag_name,
                        COUNT(e.expense_id) as usage_count,
                        SUM(e.amount) as total_amount,
                        AVG(e.amount) as average_amount
                    FROM Expense e
                    LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
                    LEFT JOIN Tags t ON te.tag_id = t.tag_id
                    LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
                    WHERE ue.username = ?
                    GROUP BY t.tag_name
                    ORDER BY total_amount DESC
                """
                params = [st.session_state.username]
            
            cursor.execute(query, params)
            data = cursor.fetchall()
            
            if data:
                df = pd.DataFrame(data, columns=["Tag", "Usage Count", "Total Amount", "Average Amount"])
                df["Average Amount"] = df["Average Amount"].round(2)
                
                # Display as table
                st.dataframe(df, use_container_width=True)
                
                # Create pie chart for amount distribution
                fig = px.pie(
                    df,
                    values='Total Amount',
                    names='Tag',
                    title='Expenses by Tag (Amount)'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Create bar chart for tag usage
                fig2 = px.bar(
                    df,
                    x='Tag',
                    y='Usage Count',
                    title='Tag Usage Frequency',
                    color='Tag'
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                log_manager.add_log(log_manager.generate_log_description("report", ["tag_expenses"]))
            else:
                st.info("No tag usage data found.")
    
    # Admin-only: Highest Spender Per Month
    elif selected_tab == "Highest Spender Per Month" and st.session_state.role == "admin":
        st.subheader("Highest Spender Per Month Report")
        
        year = st.selectbox("Select Year", list(range(datetime.now().year, datetime.now().year - 10, -1)), 
                        key="highest_spender_year")
        
        if st.button("Generate Highest Spender Report"):
            query = """
                SELECT 
                    strftime('%m', e.date) as month,
                    ue.username,
                    SUM(e.amount) as total_amount
                FROM Expense e
                LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
                WHERE strftime('%Y', e.date) = ?
                GROUP BY strftime('%m', e.date), ue.username
                ORDER BY month, total_amount DESC
            """
            params = [str(year)]
            
            cursor.execute(query, params)
            data = cursor.fetchall()
            
            if data:
                # Find highest spender for each month
                months = {}
                for month, username, amount in data:
                    month_name = {
                        '01': 'January', '02': 'February', '03': 'March', '04': 'April',
                        '05': 'May', '06': 'June', '07': 'July', '08': 'August',
                        '09': 'September', '10': 'October', '11': 'November', '12': 'December'
                    }[month]
                    
                    if month not in months:
                        months[month] = {
                            'month_name': month_name,
                            'username': username,
                            'amount': amount
                        }
                
                result = []
                for month in sorted(months.keys()):
                    result.append([
                        months[month]['month_name'],
                        months[month]['username'],
                        months[month]['amount']
                    ])
                
                df = pd.DataFrame(result, columns=["Month", "Highest Spender", "Total Amount"])
                
                # Display as table
                st.dataframe(df, use_container_width=True)
                
                # Create bar chart
                fig = px.bar(
                    df,
                    x='Month',
                    y='Total Amount',
                    color='Highest Spender',
                    title=f'Highest Spender Per Month ({year})',
                    text='Total Amount'
                )
                fig.update_layout(xaxis={'categoryorder':'array', 'categoryarray':list(month_name.values())})
                st.plotly_chart(fig, use_container_width=True)
                
                log_manager.add_log(log_manager.generate_log_description("report", ["highest_spender_per_month", str(year)]))
            else:
                st.info(f"No expense data found for year {year}.")
    
    # Show report information
    with st.expander("About Reports"):
        st.markdown("""
        ### Report Information
        
        This page provides a collection of basic reports to analyze expense patterns and trends:
        
        - **Top Expenses**: View the highest expense transactions for a selected period
        - **Category Spending**: Analyze spending patterns for a specific category
        - **Monthly Category Spending**: View spending by category across months
        - **Payment Method Usage**: Analyze which payment methods are used most frequently
        - **Frequent Category**: See which expense categories are used most often
        - **Tag Expenses**: Analyze expenses grouped by tags
        
        For more advanced analytics, try the Advanced Analytics page.
        """)