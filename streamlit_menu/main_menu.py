import streamlit as st

# from streamlit_menu.config import api_headers
from streamlit_menu.login import login_page
from streamlit_menu.customer_page import customers_page
from streamlit_menu.dashboards import dashboard_page
from streamlit_menu.tickets_page import tickets_page
from streamlit_menu.user import users_page
from streamlit_menu.search import search_page

st.set_page_config("Smart Support Desk", layout="wide")

# -----------------------
# UI Styling
# -----------------------
st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 1rem;
}

[data-testid="metric-container"] {
    background-color: #0f172a;
    padding: 18px;
    border-radius: 12px;
    color: white;
}

.section {
    padding: 1rem;
    border-radius: 12px;
    background-color: #020617;
    margin-bottom: 1rem;
}

.stDataFrame {
    border-radius: 12px;
}

section[data-testid="stSidebar"] {
    background-color: #E6E6FA;
}
</style>
""", unsafe_allow_html=True)

# -----------------------
# App Router
# -----------------------
if "token" not in st.session_state:
    login_page()
else:
    st.sidebar.markdown("## 🧠 Smart Support Desk")
    st.sidebar.caption(f"Role: {st.session_state['role'].upper()}")
    st.sidebar.divider()

    menu = ["Dashboard", "Customers", "Tickets", "Search"]
    if st.session_state["role"] == "admin":
        menu.append("Users")
    menu.append("Logout")

    choice = st.sidebar.radio("Navigate", menu)

    if choice == "Dashboard":
        dashboard_page()

    elif choice == "Customers":
        customers_page()

    elif choice == "Tickets":
        tickets_page()

    elif choice == "Users":
        users_page()

    elif choice == "Search":
        search_page()

    elif choice == "Logout":
        st.session_state.clear()
        st.rerun()
