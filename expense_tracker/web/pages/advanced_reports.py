import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from expense_tracker.database.connection import get_connection
from expense_tracker.core.reporting import ReportManager
from expense_tracker.utils.logs import LogManager

def show_advanced_reports():
    st.markdown("<div class='main-header'>Advanced Analytics</div>", unsafe_allow_html=True)

    # Initialize DB connection and managers
    conn, cursor = get_connection()
     
    report_manager = ReportManager(cursor, conn)
    report_manager.set_user_info(st.session_state.username, st.session_state.role)

    log_manager = LogManager(cursor, conn)
    log_manager.set_current_user(st.session_state.username)

     # Tabs
    tabs = st.tabs(["Above Average Expenses", "Analytics Dashboard", "Payment Method Details"])

    # Tab 1: Above Average Expenses
    with tabs[0]:
        st.subheader("Above Average Expenses")
        df = report_manager.get_above_average_expenses()
        if df.empty:
            st.info("No expenses found above category average.")
        else:
            st.dataframe(df, use_container_width=True)
            fig = px.bar(
                df,
                x="Percent Above Avg",
                y="Category",
                color="Category",
                orientation="h",
                title="Expenses Above Average (%)"
            )
            st.plotly_chart(fig, use_container_width=True)
            fig2 = px.scatter(
                df,
                x="Category Avg",
                y="Amount",
                color="Category",
                size="Amount",
                hover_name="Description",
                title="Expense vs. Category Average"
            )
            fig2.add_shape(
                type="line",
                x0=df["Category Avg"].min(),
                y0=df["Category Avg"].min(),
                x1=df["Category Avg"].max(),
                y1=df["Category Avg"].max(),
                line=dict(color="gray", dash="dash")
            )
            st.plotly_chart(fig2, use_container_width=True)
        log_manager.add_log("Viewed Above Average Expense Report")

    # Tab 2: Expense Analytics Dashboard
    with tabs[1]:
        st.subheader("Analytics Dashboard")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.today().replace(day=1))
        with col2:
            end_date = st.date_input("End Date", value=datetime.today())

        if start_date > end_date:
            st.warning("Start date must be before end date.")
            return

        df = report_manager.get_expenses_by_date_range(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )

        if df.empty:
            st.info("No data available in the selected range.")
            return

        df["date"] = pd.to_datetime(df["date"])
        df["month"] = df["date"].dt.strftime("%Y-%m")

        # Time trend chart
        trend = df.groupby("month")["amount"].sum().reset_index()
        fig = px.line(trend, x="month", y="amount", title="Monthly Expense Trend", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        # Category-wise summary
        cat_sum = df.groupby("category")["amount"].agg(["sum", "mean", "count"]).reset_index()
        st.dataframe(cat_sum.rename(columns={"sum": "Total", "mean": "Average", "count": "Transactions"}))

        # Fix: Use the correct column name "sum" instead of "Total" since rename doesn't change the actual column names
        fig2 = px.pie(cat_sum, values="sum", names="category", title="Category Distribution")
        st.plotly_chart(fig2, use_container_width=True)

        log_manager.add_log("Viewed Expense Analytics Dashboard")

    # Tab 3: Payment Method Details
    with tabs[2]:
        st.subheader("Payment Method Analysis")

        cursor.execute("SELECT payment_method_name FROM Payment_Method")
        methods = [row[0] for row in cursor.fetchall()]

        selected = st.selectbox("Payment Method", methods)

        df = report_manager.get_expenses_by_payment_method(selected)

        if df.empty:
            st.info("No data found for selected method.")
            return

        df["masked"] = df["payment_detail_identifier"].apply(
            lambda x: f"{x[:2]}{'*'*(len(x)-4)}{x[-2:]}" if x and len(x) >= 4 else x
        )
        df_display = df.drop(columns=["payment_detail_identifier"]).rename(columns={"masked": "Masked Details"})
        st.dataframe(df_display, use_container_width=True)

        summary = df.groupby("masked")["amount"].agg(["sum", "count"]).reset_index()
        fig = px.bar(summary, x="masked", y="sum", title="Expense by Payment Detail", color="count")
        st.plotly_chart(fig, use_container_width=True)

        log_manager.add_log(f"Viewed Payment Method Report: {selected}")
