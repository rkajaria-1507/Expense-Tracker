import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from reporting import ReportManager
from logs import LogManager

def show_advanced_reports():
    st.markdown("<div class='main-header'>Advanced Analytics</div>", unsafe_allow_html=True)
    
    # Get database connection and managers
    conn = sqlite3.connect("ExpenseReport", check_same_thread=False)
    cursor = conn.cursor()
    report_manager = ReportManager(cursor, conn)
    report_manager.set_user_info(st.session_state.username, st.session_state.role)
    log_manager = LogManager(cursor, conn)
    log_manager.set_current_user(st.session_state.username)
    
    # Create tabs for different advanced report types
    tabs = ["Above Average Expenses", "Expense Analytics Dashboard", "Payment Method Details"]
    
    selected_tab = st.selectbox("Select Advanced Report Type", tabs)
    
    # Report: Above Average Expenses
    if selected_tab == "Above Average Expenses":
        st.subheader("Above Average Expenses Report")
        
        if st.button("Generate Above Average Expenses Report"):
            # Build the query based on user role
            if st.session_state.role == "admin":
                query = """
                    WITH CategoryAverages AS (
                        SELECT 
                            c.category_id,
                            c.category_name,
                            AVG(e.amount) as avg_amount
                        FROM Expense e
                        JOIN category_expense ce ON e.expense_id = ce.expense_id
                        JOIN Categories c ON ce.category_id = c.category_id
                        GROUP BY c.category_id, c.category_name
                    )
                    SELECT 
                        e.expense_id,
                        e.date,
                        e.amount,
                        e.description,
                        c.category_name,
                        ca.avg_amount as category_avg,
                        (e.amount - ca.avg_amount) as amount_difference,
                        (e.amount / ca.avg_amount * 100 - 100) as percent_above_avg,
                        ue.username
                    FROM Expense e
                    JOIN category_expense ce ON e.expense_id = ce.expense_id
                    JOIN Categories c ON ce.category_id = c.category_id
                    JOIN CategoryAverages ca ON c.category_id = ca.category_id
                    JOIN user_expense ue ON e.expense_id = ue.expense_id
                    WHERE e.amount > ca.avg_amount
                    ORDER BY percent_above_avg DESC
                """
                params = []
            else:
                query = """
                    WITH CategoryAverages AS (
                        SELECT 
                            c.category_id,
                            c.category_name,
                            AVG(e.amount) as avg_amount
                        FROM Expense e
                        JOIN category_expense ce ON e.expense_id = ce.expense_id
                        JOIN Categories c ON ce.category_id = c.category_id
                        JOIN user_expense ue ON e.expense_id = ue.expense_id
                        WHERE ue.username = ?
                        GROUP BY c.category_id, c.category_name
                    )
                    SELECT 
                        e.expense_id,
                        e.date,
                        e.amount,
                        e.description,
                        c.category_name,
                        ca.avg_amount as category_avg,
                        (e.amount - ca.avg_amount) as amount_difference,
                        (e.amount / ca.avg_amount * 100 - 100) as percent_above_avg
                    FROM Expense e
                    JOIN category_expense ce ON e.expense_id = ce.expense_id
                    JOIN Categories c ON ce.category_id = c.category_id
                    JOIN CategoryAverages ca ON c.category_id = ca.category_id
                    JOIN user_expense ue ON e.expense_id = ue.expense_id
                    WHERE e.amount > ca.avg_amount
                    AND ue.username = ?
                    ORDER BY percent_above_avg DESC
                """
                params = [st.session_state.username, st.session_state.username]
            
            cursor.execute(query, params)
            expenses = cursor.fetchall()
            
            if expenses:
                # Convert to DataFrame
                if st.session_state.role == "admin":
                    columns = [
                        "ID", "Date", "Amount", "Description", "Category", 
                        "Category Avg", "Difference", "Percent Above Avg", "User"
                    ]
                else:
                    columns = [
                        "ID", "Date", "Amount", "Description", "Category", 
                        "Category Avg", "Difference", "Percent Above Avg"
                    ]
                
                df = pd.DataFrame(expenses, columns=columns)
                
                # Round numerical columns
                for col in ["Amount", "Category Avg", "Difference"]:
                    df[col] = df[col].round(2)
                df["Percent Above Avg"] = df["Percent Above Avg"].round(1)
                
                # Display summary
                st.write(f"Found {len(df)} expenses that are above their category average.")
                
                # Display as table
                st.dataframe(df, use_container_width=True)
                
                # Create bar chart showing the percent above average
                fig = px.bar(
                    df,
                    x="Percent Above Avg",
                    y="Category",
                    color="Category",
                    title="Expenses Above Category Average (%)",
                    orientation="h",
                    height=600
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Create scatter plot of amount vs category average
                fig2 = px.scatter(
                    df,
                    x="Category Avg",
                    y="Amount",
                    color="Category",
                    size="Amount",
                    hover_name="Description",
                    title="Expense Amount vs. Category Average",
                    labels={"Category Avg": "Category Average", "Amount": "Expense Amount"}
                )
                # Add diagonal line representing y=x (amount = category_avg)
                fig2.add_shape(
                    type="line",
                    x0=df["Category Avg"].min(),
                    y0=df["Category Avg"].min(),
                    x1=df["Category Avg"].max(),
                    y1=df["Category Avg"].max(),
                    line=dict(color="gray", dash="dash")
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                log_manager.add_log(log_manager.generate_log_description("report", ["above_average_expenses"]))
            else:
                st.info("No expenses found that are above their category average.")

    # Report: Expense Analytics Dashboard
    elif selected_tab == "Expense Analytics Dashboard":
        st.subheader("Expense Analytics Dashboard")
        
        # Define filter options
        st.markdown("### Filter Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Get available categories
            cursor.execute("SELECT category_name FROM Categories")
            categories = [cat[0] for cat in cursor.fetchall()]
            selected_category = st.selectbox("Category", ["All"] + categories)
        
        with col2:
            # Get available payment methods
            cursor.execute("SELECT payment_method_name FROM Payment_Method")
            payment_methods = [pm[0] for pm in cursor.fetchall()]
            selected_payment = st.selectbox("Payment Method", ["All"] + payment_methods)
        
        with col3:
            # Get available tags
            cursor.execute("SELECT DISTINCT tag_name FROM Tags")
            tags = [tag[0] for tag in cursor.fetchall()]
            selected_tag = st.selectbox("Tag", ["All"] + tags)
        
        # Date range filter
        date_range = st.date_input("Date Range", value=[])
        
        # Amount range filter
        col1, col2 = st.columns(2)
        with col1:
            min_amount = st.number_input("Min Amount", value=0.0, min_value=0.0, format="%.2f")
        with col2:
            max_amount = st.number_input("Max Amount", value=None, format="%.2f")
        
        # Special filters for admin
        if st.session_state.role == "admin":
            # Filter by user
            cursor.execute("SELECT username FROM User")
            users = [user[0] for user in cursor.fetchall()]
            selected_user = st.selectbox("User", ["All"] + users)
        
        # Generate dashboard button
        if st.button("Generate Analytics Dashboard"):
            # Build the base query
            query = """
                SELECT 
                    e.expense_id, e.date, e.amount, e.description,
                    c.category_name, t.tag_name, pm.payment_method_name
            """
            
            # Add username column for admin
            if st.session_state.role == "admin":
                query += ", ue.username"
                
            query += """
                FROM Expense e
                LEFT JOIN category_expense ce ON e.expense_id = ce.expense_id
                LEFT JOIN Categories c ON ce.category_id = c.category_id
                LEFT JOIN tag_expense te ON e.expense_id = te.expense_id
                LEFT JOIN Tags t ON te.tag_id = t.tag_id
                LEFT JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
                LEFT JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                LEFT JOIN user_expense ue ON e.expense_id = ue.expense_id
                WHERE 1=1
            """
            
            params = []
            
            # Add filter conditions
            # User filter (regular users are automatically filtered to their own expenses)
            if st.session_state.role != "admin":
                query += " AND ue.username = ?"
                params.append(st.session_state.username)
            elif selected_user != "All":
                query += " AND ue.username = ?"
                params.append(selected_user)
            
            # Category filter
            if selected_category != "All":
                query += " AND c.category_name = ?"
                params.append(selected_category)
            
            # Payment method filter
            if selected_payment != "All":
                query += " AND pm.payment_method_name = ?"
                params.append(selected_payment)
            
            # Tag filter
            if selected_tag != "All":
                query += " AND t.tag_name = ?"
                params.append(selected_tag)
            
            # Date range filter
            if date_range:
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    query += " AND e.date BETWEEN ? AND ?"
                    params.append(start_date.strftime("%Y-%m-%d"))
                    params.append(end_date.strftime("%Y-%m-%d"))
                elif len(date_range) == 1:
                    single_date = date_range[0]
                    query += " AND e.date = ?"
                    params.append(single_date.strftime("%Y-%m-%d"))
            
            # Amount range filter
            if min_amount > 0:
                query += " AND e.amount >= ?"
                params.append(min_amount)
            
            if max_amount and max_amount > 0:
                query += " AND e.amount <= ?"
                params.append(max_amount)
            
            # Execute the query
            cursor.execute(query, params)
            expenses = cursor.fetchall()
            
            if expenses:
                # Convert to DataFrame
                if st.session_state.role == "admin":
                    columns = ["ID", "Date", "Amount", "Description", "Category", "Tag", "Payment Method", "User"]
                else:
                    columns = ["ID", "Date", "Amount", "Description", "Category", "Tag", "Payment Method"]
                
                df = pd.DataFrame(expenses, columns=columns)
                df["Date"] = pd.to_datetime(df["Date"])
                
                # Display filtered expenses count and total
                st.metric("Total Filtered Expenses", len(df))
                st.metric("Total Amount", f"${df['Amount'].sum():.2f}")
                
                # Create tabs for different visualizations
                viz_tabs = st.tabs([
                    "Expenses Table", "Time Analysis", "Category Analysis", 
                    "Tag Analysis", "Payment Analysis"
                ])
                
                # Tab 1: Expenses Table
                with viz_tabs[0]:
                    st.dataframe(df, use_container_width=True)
                
                # Tab 2: Time Analysis
                with viz_tabs[1]:
                    st.subheader("Expense Trends Over Time")
                    
                    # Group by day, week, month options
                    time_group = st.radio(
                        "Group By",
                        ["Daily", "Weekly", "Monthly"],
                        horizontal=True
                    )
                    
                    if time_group == "Daily":
                        df['period'] = df['Date'].dt.date
                    elif time_group == "Weekly":
                        df['period'] = df['Date'].dt.isocalendar().week.astype(str) + '-' + df['Date'].dt.year.astype(str)
                    else:  # Monthly
                        df['period'] = df['Date'].dt.to_period('M').astype(str)
                    
                    time_data = df.groupby('period')['Amount'].agg(['sum', 'mean', 'count']).reset_index()
                    
                    fig = px.line(
                        time_data, 
                        x='period', 
                        y='sum',
                        title=f'{time_group} Expense Trend',
                        markers=True,
                        labels={'sum': 'Total Amount', 'period': 'Time Period'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Create columns for metrics
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Average Daily Expense", f"${df.groupby(df['Date'].dt.date)['Amount'].sum().mean():.2f}")
                    with col2:
                        if not df.empty:
                            max_day = df.groupby(df['Date'].dt.date)['Amount'].sum().idxmax()
                            max_amount = df.groupby(df['Date'].dt.date)['Amount'].sum().max()
                            st.metric("Highest Spending Day", f"{max_day} (${max_amount:.2f})")
                
                # Tab 3: Category Analysis
                with viz_tabs[2]:
                    st.subheader("Category Analysis")
                    
                    # Group by category
                    category_data = df.groupby('Category')['Amount'].agg(['sum', 'mean', 'count']).reset_index()
                    category_data.columns = ['Category', 'Total Amount', 'Average Amount', 'Count']
                    
                    # Display category data table
                    st.dataframe(category_data, use_container_width=True)
                    
                    # Create pie chart for category distribution
                    fig = px.pie(
                        df,
                        values='Amount',
                        names='Category',
                        title='Expense Distribution by Category'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Create bar chart for category count
                    fig2 = px.bar(
                        category_data,
                        x='Category',
                        y='Count',
                        title='Number of Expenses by Category',
                        color='Category'
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Tab 4: Tag Analysis
                with viz_tabs[3]:
                    st.subheader("Tag Analysis")
                    
                    # Group by tag
                    tag_data = df.groupby('Tag')['Amount'].agg(['sum', 'mean', 'count']).reset_index()
                    tag_data.columns = ['Tag', 'Total Amount', 'Average Amount', 'Count']
                    
                    # Display tag data table
                    st.dataframe(tag_data, use_container_width=True)
                    
                    # Create pie chart for tag distribution
                    fig = px.pie(
                        df,
                        values='Amount',
                        names='Tag',
                        title='Expense Distribution by Tag'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Create histogram for expense amounts by tag
                    fig2 = px.histogram(
                        df,
                        x='Amount',
                        color='Tag',
                        title='Expense Amount Distribution by Tag',
                        nbins=20
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Tab 5: Payment Analysis
                with viz_tabs[4]:
                    st.subheader("Payment Method Analysis")
                    
                    # Group by payment method
                    payment_data = df.groupby('Payment Method')['Amount'].agg(['sum', 'mean', 'count']).reset_index()
                    payment_data.columns = ['Payment Method', 'Total Amount', 'Average Amount', 'Count']
                    
                    # Display payment data table
                    st.dataframe(payment_data, use_container_width=True)
                    
                    # Create pie chart for payment method distribution
                    fig = px.pie(
                        df,
                        values='Amount',
                        names='Payment Method',
                        title='Expense Distribution by Payment Method'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Create bar chart comparing average transaction value by payment method
                    fig2 = px.bar(
                        payment_data,
                        x='Payment Method',
                        y='Average Amount',
                        title='Average Transaction Value by Payment Method',
                        color='Payment Method'
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                
                log_manager.add_log(log_manager.generate_log_description("report", ["analyze_expenses"]))
            else:
                st.info("No expenses found matching your filter criteria.")

    # Report: Payment Method Details with Masked Information
    elif selected_tab == "Payment Method Details":
        st.subheader("Payment Method Details Report")
        
        # Get available payment methods
        cursor.execute("SELECT payment_method_name FROM Payment_Method")
        payment_methods = [pm[0] for pm in cursor.fetchall()]
        
        if not payment_methods:
            st.warning("No payment methods found in the system.")
        else:
            selected_payment = st.selectbox("Select Payment Method", payment_methods, key="payment_details_select")
            
            if st.button("Generate Payment Method Details Report"):
                # Build the query based on user role
                if st.session_state.role == "admin":
                    query = """
                        SELECT 
                            e.expense_id, e.date, e.amount, e.description,
                            pme.payment_detail_identifier, ue.username
                        FROM Expense e
                        JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
                        JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                        JOIN user_expense ue ON e.expense_id = ue.expense_id
                        WHERE pm.payment_method_name = ?
                        ORDER BY e.date DESC
                    """
                    params = [selected_payment]
                else:
                    query = """
                        SELECT 
                            e.expense_id, e.date, e.amount, e.description,
                            pme.payment_detail_identifier
                        FROM Expense e
                        JOIN payment_method_expense pme ON e.expense_id = pme.expense_id
                        JOIN Payment_Method pm ON pme.payment_method_id = pm.payment_method_id
                        JOIN user_expense ue ON e.expense_id = ue.expense_id
                        WHERE pm.payment_method_name = ? AND ue.username = ?
                        ORDER BY e.date DESC
                    """
                    params = [selected_payment, st.session_state.username]
                
                cursor.execute(query, params)
                expenses = cursor.fetchall()
                
                if expenses:
                    # Convert to DataFrame
                    if st.session_state.role == "admin":
                        columns = ["ID", "Date", "Amount", "Description", "Payment Details", "User"]
                    else:
                        columns = ["ID", "Date", "Amount", "Description", "Payment Details"]
                    
                    df = pd.DataFrame(expenses, columns=columns)
                    
                    # Function to mask payment details for privacy
                    def mask_payment_details(details):
                        if not details or len(details) < 4:
                            return details
                        return f"{details[:2]}{'*' * (len(details) - 4)}{details[-2:]}"
                    
                    # Apply masking to payment details
                    df["Masked Details"] = df["Payment Details"].apply(mask_payment_details)
                    
                    # Display as table
                    st.dataframe(df.drop("Payment Details", axis=1), use_container_width=True)
                    
                    # Summarize payment details usage
                    if df["Masked Details"].notna().sum() > 0:
                        st.subheader("Payment Details Analysis")
                        
                        # Count unique payment details
                        unique_details = df["Payment Details"].nunique()
                        st.metric("Unique Payment Methods", unique_details)
                        
                        # Create a chart of expense amounts by payment detail
                        if unique_details > 1:
                            # Group by masked payment details for privacy
                            detail_data = df.groupby("Masked Details")["Amount"].agg(["sum", "count"]).reset_index()
                            detail_data.columns = ["Payment Detail", "Total Amount", "Number of Transactions"]
                            
                            fig = px.bar(
                                detail_data,
                                x="Payment Detail",
                                y="Total Amount",
                                color="Number of Transactions",
                                title=f"Expense Amounts by Payment Detail ({selected_payment})",
                                labels={"Total Amount": "Total Amount", "Payment Detail": "Payment Detail (Masked)"}
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    
                    log_manager.add_log(log_manager.generate_log_description("report", ["payment_method_details_expense"]))
                else:
                    st.info(f"No expenses found for payment method '{selected_payment}'.")
    
    # Show information about advanced reports
    with st.expander("About Advanced Analytics"):
        st.markdown("""
        ### Advanced Analytics Information
        
        This page provides more sophisticated analysis tools:
        
        - **Above Average Expenses**: Identify expenses that exceed the average for their category
        - **Expense Analytics Dashboard**: Comprehensive analysis with multiple visualization options
        - **Payment Method Details**: Analyze expenses by payment method with privacy protection
        
        These reports help identify spending patterns and anomalies in your expense data.
        """)