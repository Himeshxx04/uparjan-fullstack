import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import date

# ================== BACKEND BASE URL ================== #

BACKEND_URL = "http://127.0.0.1:8000"   # FastAPI backend


# ================== AUTH SESSION STATE ================== #

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False


# ================== PAGE CONFIG ================== #

st.set_page_config(
    page_title="Uparjan Full-Stack",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("💰 Uparjan – Full-Stack Personal Finance App")


# ================== AUTH HEADERS HELPER ================== #

def get_auth_headers():
    """
    Build Authorization header if we have a JWT from login.
    This will be added to every backend request.
    """
    headers = {}
    if st.session_state.access_token:
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    return headers


# ================== API HELPERS ================== #

def api_get(path: str):
    """Helper for GET requests to the backend."""
    try:
        resp = requests.get(
            f"{BACKEND_URL}{path}",
            headers=get_auth_headers()
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, str(e)


def api_post(path: str, payload: dict):
    """Helper for POST requests to the backend."""
    try:
        resp = requests.post(
            f"{BACKEND_URL}{path}",
            json=payload,
            headers=get_auth_headers()
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, str(e)


def api_delete(path: str):
    """Helper for DELETE requests to the backend."""
    try:
        resp = requests.delete(
            f"{BACKEND_URL}{path}",
            headers=get_auth_headers()
        )
        resp.raise_for_status()
        return True, None
    except requests.RequestException as e:
        return False, str(e)


# ================== TRANSACTION STATE ================== #

if "transactions" not in st.session_state:
    # Will hold a list of transactions from backend
    st.session_state.transactions = []


def load_transactions_into_state():
    """
    Fetch all transactions from the FastAPI backend
    and store them in st.session_state.transactions.
    """
    data, err = api_get("/transactions")
    if err:
        st.error(f"Failed to load transactions from backend: {err}")
        return

    # Expecting list of dicts like:
    # { "id": ..., "type": "Income"/"Expense", "category": "...", "amount": ..., "date": "YYYY-MM-DD" }
    st.session_state.transactions = data


# ================== SIDEBAR NAVIGATION ================== #

st.sidebar.title("📚 Navigation")

page = st.sidebar.selectbox(
    "Navigate",
    [
        "Login / Register",
        "Home",
        "Add Transaction",
        "Dashboard",
        "Stock Tracker",
    ],
)

st.sidebar.markdown("---")
if st.session_state.is_authenticated:
    st.sidebar.success(f"Logged in as: {st.session_state.user_email}")
    if st.sidebar.button("Logout"):
        st.session_state.access_token = None
        st.session_state.user_email = None
        st.session_state.is_authenticated = False
        st.session_state.transactions = []
        st.sidebar.info("Logged out.")
else:
    st.sidebar.info("Not logged in.")

st.sidebar.markdown("👨‍💻 **Uparjan – Full Stack Demo**")
st.sidebar.markdown("🖥️ Frontend: Streamlit")
st.sidebar.markdown("🧩 Backend: FastAPI + SQLite (SQLAlchemy)")


# ================== PAGE: LOGIN / REGISTER ================== #

if page == "Login / Register":
    st.header("🔐 Authentication")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    # ---------- LOGIN TAB ---------- #
    with tab_login:
        st.subheader("Login")

        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            if not login_email or not login_password:
                st.warning("Please enter both email and password.")
            else:
                payload = {
                    "email": login_email,
                    "password": login_password,
                }
                data, err = api_post("/auth/login", payload)
                if err:
                    st.error(f"Login failed: {err}")
                else:
                    # Expecting backend to return: { "access_token": "...", "token_type": "bearer" }
                    token = data.get("access_token")
                    if not token:
                        st.error("Login response did not contain an access_token.")
                    else:
                        st.session_state.access_token = token
                        st.session_state.user_email = login_email
                        st.session_state.is_authenticated = True
                        st.success("✅ Logged in successfully!")

    # ---------- REGISTER TAB ---------- #
    with tab_register:
        st.subheader("Register new account")

        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_password2 = st.text_input("Confirm Password", type="password", key="reg_password2")

        if st.button("Register"):
            if not reg_email or not reg_password or not reg_password2:
                st.warning("Please fill all fields.")
            elif reg_password != reg_password2:
                st.warning("Passwords do not match.")
            else:
                payload = {
                    "email": reg_email,
                    "password": reg_password,
                }
                data, err = api_post("/auth/register", payload)
                if err:
                    st.error(f"Registration failed: {err}")
                else:
                    st.success("🎉 Registration successful! You can now log in.")


# ---------------- GATE OTHER PAGES IF NOT LOGGED IN ---------------- #

elif not st.session_state.is_authenticated:
    # If user tries to go to other pages without login
    st.warning("You must be logged in to access this page. Go to 'Login / Register' first.")


# ================== PAGE: HOME ================== #

elif page == "Home":
    st.header("🏠 Welcome")

    health, err = api_get("/health")
    if err:
        st.error(f"Backend health check failed: {err}")
    else:
        st.success(f"Backend status: {health.get('status', 'unknown')}")

    st.write(
        """
        This is the **full-stack** version of Uparjan.

        **Architecture:**
        - **Frontend:** Streamlit (this `app.py` file)
        - **Backend API:** FastAPI (`backend/main.py`) at `http://127.0.0.1:8000`
        - **Database:** SQLite (`transactions.db`) managed via SQLAlchemy in the backend

        The Streamlit app never talks to the database directly.
        All create/read/delete operations for transactions go through the FastAPI REST API.
        """
    )


# ================== PAGE: ADD TRANSACTION ================== #

elif page == "Add Transaction":
    st.header("💸 Add / Manage Transactions")

    # ---- Add transaction form ---- #
    with st.form("add_tx_form"):
        t_type = st.selectbox("Type", ["Income", "Expense"])
        category = st.text_input("Category (e.g., Food, Rent, Salary)")
        amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
        tx_date = st.date_input("Date", value=date.today())

        submitted = st.form_submit_button("➕ Add Transaction")

    if submitted:
        if not category or amount <= 0:
            st.warning("Please provide a valid category and amount > 0.")
        else:
            payload = {
                "type": t_type,          # must match FastAPI schema field names
                "category": category,
                "amount": amount,
                "date": str(tx_date),    # ISO format string: 'YYYY-MM-DD'
            }
            created, err = api_post("/transactions", payload)
            if err:
                st.error(f"Failed to create transaction: {err}")
            else:
                st.success("✅ Transaction added successfully.")
                load_transactions_into_state()

    # ---- Refresh + display current transactions ---- #
    if st.button("🔄 Refresh transactions from backend"):
        load_transactions_into_state()

    if st.session_state.transactions:
        df = pd.DataFrame(st.session_state.transactions)
        st.subheader("🧾 Current Transactions")
        st.dataframe(df, use_container_width=True)

        # ---- Delete section ---- #
        st.markdown("### 🗑️ Delete a transaction")
        ids = [tx["id"] for tx in st.session_state.transactions]
        selected_id = st.selectbox("Select transaction ID to delete", ids)

        if st.button("Delete selected"):
            ok, err = api_delete(f"/transactions/{selected_id}")
            if err or not ok:
                st.error(f"Failed to delete: {err}")
            else:
                st.success(f"✅ Deleted transaction with id={selected_id}")
                load_transactions_into_state()
    else:
        st.info("No transactions yet. Add your first one above.")


# ================== PAGE: DASHBOARD ================== #

elif page == "Dashboard":
    st.header("📊 Dashboard")

    # Ensure we have data
    if not st.session_state.transactions:
        load_transactions_into_state()

    if not st.session_state.transactions:
        st.warning("No transactions found in backend. Add some first.")
    else:
        df = pd.DataFrame(st.session_state.transactions)

        # Normalize column names (in case backend uses lower-case)
        # Expecting keys: id, type, category, amount, date
        if "date" not in df.columns:
            st.error("Backend JSON format not as expected (missing 'date').")
        else:
            # Ensure proper types
            df["date"] = pd.to_datetime(df["date"]).dt.date

            st.subheader("🔍 Filters")
            categories = ["All"] + sorted(df["category"].unique().tolist())
            selected_cat = st.selectbox("Category", categories)

            min_date = df["date"].min()
            max_date = df["date"].max()
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start date", min_date)
            with col2:
                end_date = st.date_input("End date", max_date)

            # Apply filters
            filtered = df[
                (df["date"] >= start_date) & (df["date"] <= end_date)
            ]
            if selected_cat != "All":
                filtered = filtered[filtered["category"] == selected_cat]

            if filtered.empty:
                st.info("No transactions match the current filter.")
            else:
                # ---- Metrics ---- #
                income = filtered.loc[filtered["type"] == "Income", "amount"].sum()
                expenses = filtered.loc[filtered["type"] == "Expense", "amount"].sum()
                savings = income - expenses

                c1, c2, c3 = st.columns(3)
                c1.metric("Total Income (₹)", f"{income:,.2f}")
                c2.metric("Total Expenses (₹)", f"{expenses:,.2f}")
                c3.metric("Savings (₹)", f"{savings:,.2f}")

                # ---- Pie chart: expenses by category ---- #
                exp_df = filtered[filtered["type"] == "Expense"]
                if not exp_df.empty:
                    fig_pie = px.pie(
                        exp_df,
                        names="category",
                        values="amount",
                        title="Expense breakdown by category",
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)

                # ---- Monthly expense trend ---- #
                tmp = filtered.copy()
                tmp["month"] = pd.to_datetime(tmp["date"]).dt.to_period("M").astype(str)
                monthly = (
                    tmp[tmp["type"] == "Expense"]
                    .groupby("month")["amount"]
                    .sum()
                    .reset_index()
                )
                if not monthly.empty:
                    fig_bar = px.bar(
                        monthly,
                        x="month",
                        y="amount",
                        title="Monthly expense trend",
                        text_auto=True,
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

                st.subheader("📄 Filtered transactions")
                st.dataframe(filtered, use_container_width=True)


# ================== PAGE: STOCK TRACKER ================== #

elif page == "Stock Tracker":
    import yfinance as yf

    st.header("💹 Stock Tracker")

    symbol = st.text_input("Enter stock symbol (e.g., AAPL, RELIANCE.NS)")
    if st.button("Get price"):
        if not symbol:
            st.warning("Please enter a symbol.")
        else:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                price = info.get("currentPrice")
                if price is None:
                    st.warning("Could not fetch price. Try a different symbol, or check spelling.")
                else:
                    st.success(f"Current price of **{symbol}**: ₹{price}")
            except Exception as e:
                st.error(f"Error fetching data: {e}")


# ================== FOOTER ================== #

st.markdown(
    """
    <hr/>
    <div style="text-align:center; color: grey;">
    © 2025 Uparjan | Full-stack demo (Streamlit + FastAPI + SQLite + JWT Auth)
    </div>
    """,
    unsafe_allow_html=True,
)
