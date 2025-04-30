import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from expense_tracker.database.connection import get_connection
from expense_tracker.core.reporting import ReportManager
from expense_tracker.utils.logs import LogManager
import streamlit as st

def show_basic_reports():
    st.markdown("<div class='main-header'>Basic Reports</div>", unsafe_allow_html=True)

    # Initialize DB connection and managers
    conn, cursor = get_connection()
    report_manager = ReportManager(cursor, conn)
    report_manager.set_user_info(st.session_state.username, st.session_state.role)
    log_manager = LogManager(cursor, conn)
    log_manager.set_current_user(st.session_state.username)

    # Tabs
    tabs = st.tabs(["Top Expenses", "Category Overview", "Time Summary"])

    # Tab 1: Top Expenses
    with tabs[0]:
        st.subheader("Top Expenses")

        col1, col2, col3 = st.columns(3)
        with col1:
            start = st.date_input("Start Date", value=datetime.today().replace(day=1))
        with col2:
            end = st.date_input("End Date", value=datetime.today())
        with col3:
            limit = st.number_input("Number to Show", min_value=1, max_value=100, value=10)

        if start and end and start <= end:
            df = report_manager.get_top_expenses(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), limit)

            if df:
                df = pd.DataFrame(df, columns=[
                    "ID", "Date", "Amount", "Description", "Category", "Tag", "Payment Method", "Username"
                ])
                if st.session_state.role != "admin":
                    df = df.drop(columns=["Username"])

                st.dataframe(df, use_container_width=True)

                fig = px.bar(
                    df,
                    x="Amount",
                    y="Description",
                    color="Category",
                    orientation="h",
                    title="Top Expenses",
                    labels={"Description": "", "Amount": "Amount ($)"},
                )
                st.plotly_chart(fig, use_container_width=True)

                log_manager.add_log("Viewed Top Expenses Report")
            else:
                st.info("No top expenses found in this range.")

    # Tab 2: Category Overview
    with tabs[1]:
        st.subheader("Category Spending Overview")

        cursor.execute("SELECT category_name FROM Categories ORDER BY category_name")
        categories = [c[0] for c in cursor.fetchall()]
        selected = st.selectbox("Select Category", categories)

        if selected:
            stats = report_manager.get_category_statistics(selected)
            if stats:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total", f"${stats['total']:.2f}")
                col2.metric("Count", stats["count"])
                # Fix: Check for both 'avg_amount' and 'average' keys
                if 'avg_amount' in stats:
                    col3.metric("Avg", f"${stats['avg_amount']:.2f}")
                elif 'average' in stats:
                    col3.metric("Avg", f"${stats['average']:.2f}")
                else:
                    # Calculate if neither key exists
                    avg = stats['total'] / stats['count'] if stats['count'] > 0 else 0
                    col3.metric("Avg", f"${avg:.2f}")
                col4.metric("Max", f"${stats['max_amount']:.2f}")

                df = report_manager.get_category_expenses(selected)
                if not df.empty:
                    df["date"] = pd.to_datetime(df["date"])
                    df["month"] = df["date"].dt.to_period("M").astype(str)
                    month_summary = df.groupby("month")["amount"].sum().reset_index()

                    fig = px.line(
                        month_summary,
                        x="month",
                        y="amount",
                        title=f"Monthly Trend for {selected}",
                        markers=True
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    st.dataframe(df[["date", "amount", "description", "tag"]], use_container_width=True)
                    log_manager.add_log(f"Viewed Category Overview: {selected}")
                else:
                    st.info("No data available for this category.")
            else:
                st.info("No statistics found.")

    # Tab 3: Time Summary
    with tabs[2]:
        st.subheader("Time Summary")

        col1, col2 = st.columns(2)
        with col1:
            start = st.date_input("Start Date", key="time_start")
        with col2:
            end = st.date_input("End Date", key="time_end")

        if start and end and start <= end:
            df = report_manager.get_expenses_by_date_range(
                start.strftime("%Y-%m-%d"),
                end.strftime("%Y-%m-%d")
            )

            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                df["month"] = df["date"].dt.strftime("%Y-%m")
                trend = df.groupby("month")["amount"].sum().reset_index()

                fig = px.bar(
                    trend,
                    x="month",
                    y="amount",
                    title="Spending Over Time",
                    labels={"month": "Month", "amount": "Total Amount"}
                )
                st.plotly_chart(fig, use_container_width=True)

                by_cat = df.groupby("category")["amount"].sum().reset_index()
                fig2 = px.pie(by_cat, values="amount", names="category", title="By Category")
                st.plotly_chart(fig2, use_container_width=True)

                st.metric("Total", f"${df['amount'].sum():.2f}")
                st.metric("Avg/Txn", f"${df['amount'].mean():.2f}")
                st.metric("Transactions", len(df))

                log_manager.add_log("Viewed Time Summary")
            else:
                st.info("No data in selected range.")
