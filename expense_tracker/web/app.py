import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from expense_tracker.core.user import UserManager
from expense_tracker.core.category import CategoryManager
from expense_tracker.core.payment import PaymentManager
from expense_tracker.core.expense import ExpenseManager
from expense_tracker.core.reporting import ReportManager
from expense_tracker.utils.csv_operations import CSVOperations
from expense_tracker.utils.logs import LogManager
from expense_tracker.database.sql_queries import USER_QUERIES

# Import centralized DB connection
from expense_tracker.database.connection import get_connection

# Import pages via package path
from expense_tracker.web.pages.user_management import show_user_management
from expense_tracker.web.pages.category_management import show_category_management
from expense_tracker.web.pages.payment_management import show_payment_management
from expense_tracker.web.pages.manage_expenses import show_manage_expenses
from expense_tracker.web.pages.basic_reports import show_basic_reports
from expense_tracker.web.pages.advanced_reports import show_advanced_reports
from expense_tracker.web.pages.import_export import show_import_export
from expense_tracker.web.pages.system_logs import show_system_logs

# Set page configuration
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
    <style>
    .main-header {
        font-size: 30px;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 20px;
    }
    .role-badge {
        background-color: #1E88E5;
        color: white;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 14px;
        font-weight: bold;
    }
    .section-header {
        font-size: 24px;
        font-weight: bold;
        color: #333;
        margin-top: 10px;
        margin-bottom: 15px;
        border-bottom: 2px solid #ddd;
        padding-bottom: 10px;
    }
    .card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #f9f9f9;
    }
    .metric-card {
        background-color: #f0f8ff;
        border-left: 4px solid #1E88E5;
    }
    .success-message {
        padding: 10px;
        background-color: #d4edda;
        color: #155724;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .error-message {
        padding: 10px;
        background-color: #f8d7da;
        color: #721c24;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .sidebar .sidebar-content {
        background-color: #f5f5f5;
    }
    .user-info {
        padding: 10px;
        background-color: #e3f2fd;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%;
    }
    .success-box {
        padding: 10px;
        background-color: #ccffcc;
        border-left: 5px solid #00cc00;
        margin: 10px 0;
    }
    .warning-box {
        padding: 10px;
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        margin: 10px 0;
    }
    .admin-badge {
        background-color: #D81B60;
    }
    
    [data-testid="stSidebarNav"] {
        display: none;
    }
    div.stButton > button {
        text-align: left !important;
        justify-content: flex-start !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for user authentication and navigation
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "login"

# Initialize managers
def initialize_managers(_conn, _cursor):
    user_manager = UserManager(_cursor, _conn)
    category_manager = CategoryManager(_cursor, _conn)
    payment_manager = PaymentManager(_cursor, _conn)
    expense_manager = ExpenseManager(_cursor, _conn)
    # Pass expense_manager directly to CSVOperations constructor
    csv_operations = CSVOperations(_cursor, _conn, expense_manager)
    report_manager = ReportManager(_cursor, _conn)
    log_manager = LogManager(_cursor, _conn)
    
    return (user_manager, category_manager, payment_manager, 
            expense_manager, csv_operations, report_manager, log_manager)

# Get database connection and initialize managers
conn, cursor = get_connection()
(user_manager, category_manager, payment_manager, 
expense_manager, csv_operations, report_manager, log_manager) = initialize_managers(conn, cursor)

# Persist objects in session_state
st.session_state.conn = conn
st.session_state.cursor = cursor
st.session_state.user_manager = user_manager
st.session_state.category_manager = category_manager
st.session_state.payment_manager = payment_manager
st.session_state.expense_manager = expense_manager
st.session_state.csv_operations = csv_operations
st.session_state.report_manager = report_manager
st.session_state.log_manager = log_manager

# Authentication Functions
def login_user(username, password):
    if user_manager.authenticate(username, password):
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.role = user_manager.privileges
        
        # Set current user in all managers
        expense_manager.set_current_user(username)
        csv_operations.set_current_user(username)
        report_manager.set_user_info(username, user_manager.privileges)
        log_manager.set_current_user(username)
        
        log_manager.add_log(log_manager.generate_log_description("login"))
        return True
    return False

def logout_user():
    if st.session_state.authenticated:
        log_manager.add_log(log_manager.generate_log_description("logout"))
        user_manager.logout()
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.current_page = "login"
        # Force a rerun to refresh the page
        st.rerun()

# Navigation functions
def navigate_to(page):
    st.session_state.current_page = page
    
# Navigation sidebar when authenticated
def show_sidebar():
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.username}!")
        st.markdown(f"<div class='role-badge'>{st.session_state.role.upper()}</div>", unsafe_allow_html=True)
        st.divider()
        
        # Dashboard for all users
        if st.sidebar.button("Dashboard", key="nav_dashboard"):
            navigate_to("dashboard")
        
        # Admin-specific navigation
        if st.session_state.role == "admin":
            st.sidebar.markdown("### Admin")
            if st.sidebar.button("User Management", key="nav_users"):
                navigate_to("user_management")
            if st.sidebar.button("Category Management", key="nav_categories"):
                navigate_to("category_management")
            if st.sidebar.button("Payment Method Management", key="nav_payment"):
                navigate_to("payment_management")
            if st.sidebar.button("System Logs", key="nav_logs"):
                navigate_to("system_logs")
        
        # User-specific navigation
        if st.session_state.role == "user":
            st.sidebar.markdown("### Expenses")
            if st.sidebar.button("Manage Expenses", key="nav_expenses"):
                navigate_to("manage_expenses")
        
        # Common navigation for both roles
        st.sidebar.markdown("### Reports")
        if st.sidebar.button("Basic Reports", key="nav_basic_reports"):
            navigate_to("basic_reports")
        if st.sidebar.button("Advanced Analytics", key="nav_advanced_reports"):
            navigate_to("advanced_reports")
        
        st.sidebar.markdown("### Data")
        if st.sidebar.button("Import/Export", key="nav_import_export"):
            navigate_to("import_export")
        
        # Delete My Account button
        st.sidebar.divider()
        if st.sidebar.button("Delete My Account", key="delete_my_account_btn"):
            navigate_to("delete_account")
        # Logout button
        st.sidebar.divider()
        if st.sidebar.button("Logout", key="logout_btn"):
            logout_user()

def show_delete_account():
    st.markdown("<div class='main-header'>Delete My Account</div>", unsafe_allow_html=True)
    # Count user-related expenses
    # Use module-level cursor
    global cursor
    user = st.session_state.username
    cursor.execute(USER_QUERIES["check_user_expenses"], (user,))
    count = cursor.fetchone()[0]
    st.warning(f"Deleting your account will remove your user data and {count} associated expenses. This action cannot be undone.")
    confirm = st.checkbox("I understand the consequences and want to delete my account", key="confirm_self_delete")
    if confirm and st.button("Delete My Account", key="confirm_delete_account_btn"):
        result = user_manager.delete_user(user)
        if result:
            st.success("Your account and all associated data have been deleted. You will be logged out.")
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.current_page = "login"
            st.rerun()
        else:
            st.error("Failed to delete your account. Please try again.")

# Login Page
def show_login_page():
    st.markdown("<div class='main-header'>💰 Expense Tracker System</div>", unsafe_allow_html=True)
    # Two tabs: Login and Sign Up
    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])
    # Login Tab
    with tab_login:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Login")
                if submitted:
                    if login_user(username, password):
                        st.success("Login successful!")
                        st.session_state.current_page = "dashboard"
                        st.rerun()
                    else:
                        st.error("Invalid username or password!")
    # Sign Up Tab
    with tab_signup:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("signup_form"):
                new_user = st.text_input("Choose a username", key="signup_username")
                new_pass = st.text_input("Choose a password", type="password", key="signup_password")
                signup = st.form_submit_button("Sign Up")
                if signup:
                    if user_manager.register(new_user, new_pass):
                        # Auto-login new user
                        if login_user(new_user, new_pass):
                            st.success("Registration successful!")
                            st.session_state.current_page = "dashboard"
                            st.rerun()
                    else:
                        st.error("Registration failed. See errors above.")
     
def show_dashboard():
    st.markdown("<div class='main-header'>Dashboard</div>", unsafe_allow_html=True)
    
    # Get expenses data
    if st.session_state.role == "admin":
        query = """
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
    else:
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
        WHERE ue.username = '{st.session_state.username}'
        """
    
    expenses_df = pd.read_sql_query(query, conn)
    
    # Quick metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='card metric-card'>", unsafe_allow_html=True)
        st.metric("Total Expenses", f"₹{expenses_df['amount'].sum():.2f}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='card metric-card'>", unsafe_allow_html=True)
        st.metric("Average Expense", (f"₹{expenses_df['amount'].mean():.2f}") if not expenses_df.empty else "₹0.00")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='card metric-card'>", unsafe_allow_html=True)
        st.metric("Expense Count", len(expenses_df))
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("<div class='card metric-card'>", unsafe_allow_html=True)
        if not expenses_df.empty:
            st.metric("Latest Expense Date", expenses_df['date'].max())
        else:
            st.metric("Latest Expense Date", "N/A")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Charts
    if not expenses_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='section-header'>Category Breakdown</div>", unsafe_allow_html=True)
            category_data = expenses_df.groupby('category_name')['amount'].sum().reset_index()
            fig = px.pie(category_data, values='amount', names='category_name', 
                        title='Expenses by Category', hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("<div class='section-header'>Monthly Trend</div>", unsafe_allow_html=True)
            expenses_df['month'] = pd.to_datetime(expenses_df['date']).dt.strftime('%Y-%m')
            monthly_data = expenses_df.groupby('month')['amount'].sum().reset_index()
            fig = px.line(monthly_data, x='month', y='amount', 
                        title='Monthly Expense Trend',
                        markers=True)
            st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='section-header'>Payment Method Usage</div>", unsafe_allow_html=True)
            payment_data = expenses_df.groupby('payment_method_name')['amount'].sum().reset_index()
            fig = px.bar(payment_data, x='payment_method_name', y='amount',
                        title='Expenses by Payment Method',
                        color='payment_method_name',
                        labels={'payment_method_name': 'Payment Method', 'amount': 'Total Amount'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("<div class='section-header'>Tag Analysis</div>", unsafe_allow_html=True)
            tag_data = expenses_df.groupby('tag_name')['amount'].sum().reset_index()
            fig = px.bar(tag_data, x='tag_name', y='amount',
                        title='Expenses by Tag',
                        color='tag_name',
                        labels={'tag_name': 'Tag', 'amount': 'Total Amount'})
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expense data available. Add some expenses to see analytics.")
    
    # Recent expenses table
    st.markdown("<div class='section-header'>Recent Expenses</div>", unsafe_allow_html=True)
    
    if not expenses_df.empty:
        recent_expenses = expenses_df.sort_values('date', ascending=False).head(10)
        recent_expenses = recent_expenses[['expense_id', 'date', 'amount', 'category_name', 'tag_name', 'payment_method_name', 'description']]
        recent_expenses.columns = ['ID', 'Date', 'Amount', 'Category', 'Tag', 'Payment Method', 'Description']
        st.dataframe(recent_expenses, use_container_width=True)
    else:
        st.info("No recent expenses to display.")

# Main app logic
def main():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = "login"

    if st.session_state.authenticated:
        show_sidebar()

        if st.session_state.current_page == "dashboard":
            show_dashboard()
        elif st.session_state.current_page == "user_management":
            show_user_management()
        elif st.session_state.current_page == "category_management":
            show_category_management()
        elif st.session_state.current_page == "payment_management":
            show_payment_management()
        elif st.session_state.current_page == "system_logs":
            show_system_logs()
        elif st.session_state.current_page == "manage_expenses":
            show_manage_expenses()
        elif st.session_state.current_page == "basic_reports":
            show_basic_reports()
        elif st.session_state.current_page == "advanced_reports":
            show_advanced_reports()
        elif st.session_state.current_page == "import_export":
            show_import_export()
        elif st.session_state.current_page == "delete_account":
            show_delete_account()
        else:
            show_dashboard()
    else:
        show_login_page()

if __name__ == "__main__":
    main()