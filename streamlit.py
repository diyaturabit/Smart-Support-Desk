# import streamlit as st
# import requests

# API_URL = "http://127.0.0.1:5000"

# st.set_page_config(page_title="Smart Support Desk", layout="wide")

# # ---------------------------
# # Helpers
# # ---------------------------
# def api_headers():
#     return {
#         "Authorization": f"Bearer {st.session_state['token']}",
#         "Content-Type": "application/json"
#     }

# def login(email, password):
#     res = requests.post(
#         f"{API_URL}/login",
#         json={"email": email, "password": password}
#     )
#     if res.status_code == 200:
#         data = res.json()
#         st.session_state["token"] = data["access_token"]
#         st.session_state["role"] = data["role"]
#         return True
#     else:
#         st.error("Invalid credentials")
#         return False

# # ---------------------------
# # Login Page
# # ---------------------------
# def login_page():
#     st.title("🔐 Login")

#     email = st.text_input("Email")
#     password = st.text_input("Password", type="password")

#     if st.button("Login"):
#         if login(email, password):
#             st.success("Login successful")
#             st.rerun()

# # ---------------------------
# # Users (ADMIN)
# # ---------------------------
# def users_page():
#     st.header("👤 User Management (Admin)")

#     email = st.text_input("User Email")
#     password = st.text_input("Password", type="password")
#     role = st.selectbox("Role", ["admin", "staff"])

#     if st.button("Create User"):
#         res = requests.post(
#             f"{API_URL}/users",
#             headers=api_headers(),
#             json={"email": email, "password": password, "role": role}
#         )
#         if res.status_code == 200:
#             st.success("User created")
#         else:
#             st.error(res.json().get("error"))

# # ---------------------------
# # Customers
# # ---------------------------
# def customers_page():
#     st.header("👥 Customers")

#     # Create
#     with st.expander("Add Customer"):
#         name = st.text_input("Name")
#         email = st.text_input("Email")
#         company = st.text_input("Company")
#         age = st.number_input("Age", min_value=1)

#         if st.button("Create Customer"):
#             res = requests.post(
#                 f"{API_URL}/create_customer",
#                 headers=api_headers(),
#                 json={
#                     "name": name,
#                     "email": email,
#                     "company": company,
#                     "age": age
#                 }
#             )
#             if res.status_code == 200:
#                 st.success("Customer added")
#                 st.rerun()

#     # View
#     res = requests.get(f"{API_URL}/get_customer", headers=api_headers())
#     if res.status_code == 200:
#         st.table(res.json())

# # ---------------------------
# # Tickets
# # ---------------------------
# def tickets_page():
#     st.header("🎫 Tickets")

#     with st.expander("Create Ticket"):
#         title = st.text_input("Title")
#         description = st.text_area("Description")
#         priority = st.selectbox("Priority", ["High", "Medium", "Low"])
#         customer_id = st.number_input("Customer ID", min_value=1)

#         if st.button("Create Ticket"):
#             res = requests.post(
#                 f"{API_URL}/create_ticket",
#                 headers=api_headers(),
#                 json={
#                     "title": title,
#                     "description": description,
#                     "priority": priority,
#                     "customer_id": customer_id
#                 }
#             )
#             if res.status_code == 200:
#                 st.success("Ticket created")
#                 st.rerun()

#     res = requests.get(f"{API_URL}/get_ticket", headers=api_headers())
#     if res.status_code == 200:
#         st.table(res.json())


# # ---------------------------
# # Main App
# # ---------------------------
# if "tusers_page()
#     elif choice == "Logout":
#         st.session_state.clear()
#         st.rerun()

# oken" not in st.session_state:
#     login_page()
# else:
#     st.sidebar.title("Navigation")

#     menu = ["Dashboard", "Customers", "Tickets"]

#     if st.session_state["role"] == "admin":
#         menu.append("Users")

#     menu.append("Logout")

#     choice = st.sidebar.radio("Go to", menu)

#     if choice == "Dashboard":
#         dashboard_page()
#     elif choice == "Customers":
#         customers_page()
#     elif choice == "Tickets":
#         tickets_page()
#     elif choice == "Users":
        

import streamlit as st
import requests

API_URL = "http://127.0.0.1:5000"

st.set_page_config("Smart Support Desk", layout="wide")

# -----------------------
# Helpers
# -----------------------
def api_headers():
    return {"Authorization": f"Bearer {st.session_state['token']}"}

def login(email, password):
    res = requests.post(f"{API_URL}/login", json={
        "email": email,
        "password": password
    })
    if res.status_code == 200:
        data = res.json()
        st.session_state["token"] = data["access_token"]
        st.session_state["role"] = data["role"]
        return True
    st.error("Invalid login")
    return False

# -----------------------
# Login Page
# -----------------------
def login_page():
    st.title("🔐 Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login(email, password):
            st.rerun()

# ---------------------------
# Dashboard
# ---------------------------
def dashboard_page():
    st.header("📊 Dashboard")

    res = requests.get(f"{API_URL}/dashboard", headers=api_headers())
    if res.status_code == 200:
        stats = res.json()
        st.metric("Total Customers", stats["total_customer"])
        st.metric("Open Tickets", stats["open"])
        st.metric("High Priority", stats["high"])
        st.metric("Medium Priority", stats["medium"])
        st.metric("Low Priority", stats["low"])


# -----------------------
# Customers
# -----------------------
def customers_page():
    st.header("👥 Customers")

    # VIEW
    res = requests.get(f"{API_URL}/get_customer", headers=api_headers())
    if res.status_code == 200:
        st.table(res.json())

    # CREATE (Admin only)
    # if st.session_state["role"] == "admin","Staff":
    st.subheader("➕ Add Customer")
    name = st.text_input("Name")
    email = st.text_input("Email")
    company = st.text_input("Company")
    age = st.number_input("Age", 1)

    if st.button("Create Customer"):
        res = requests.post(
            f"{API_URL}/create_customer",
            headers=api_headers(),
            json={"name": name, "email": email, "company": company, "age": age}
        )
        if res.status_code == 200:
            st.success("Customer created")
            st.rerun()

    # UPDATE / DELETE
    st.subheader("✏️ Update / ❌ Delete")
    cid = st.number_input("Customer ID", 1)

    col1, col2= st.columns(2)

    with col1:
        if st.button("Update Customer"):
            res = requests.put(
                f"{API_URL}/update_customer/{cid}",
                headers=api_headers(),
                json={"name": name, "email": email, "company": company, "age": age}
            )
            if res.status_code == 200:
                st.success("Updated")
                st.rerun()

    with col2:
        if st.button("Delete Customer"):
            res = requests.delete(
                f"{API_URL}/delete_customer/{cid}",
                headers=api_headers()
            )
            if res.status_code == 200:
                st.success("Deleted")
                st.rerun()
  

# -----------------------
# Tickets
# -----------------------
def tickets_page():
    st.header("🎫 Tickets")

    # FILTERS
    status = st.selectbox("Status", ["", "Open", "Closed"])
    priority = st.selectbox("Priority", ["", "High", "Medium", "Low"])

    params = {}
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority

    res = requests.get(
        f"{API_URL}/tickets",
        headers=api_headers(),
        params=params
    )
    if res.status_code == 200:
        st.table(res.json()["tickets"])

    # CREATE
    st.subheader("➕ Create Ticket")
    title = st.text_input("Title")
    description = st.text_area("Description")
    priority = st.selectbox("Priority", ["High", "Medium", "Low"], key="p")
    customer_id = st.number_input("Customer ID", 1)

    if st.button("Create Ticket"):
        res = requests.post(
            f"{API_URL}/create_ticket",
            headers=api_headers(),
            json={
                "title": title,
                "description": description,
                "priority": priority,
                "customer_id": customer_id
            }
        )
        if res.status_code == 200:
            st.success("Ticket created")
            st.rerun()

    # UPDATE / DELETE
    st.subheader("✏️ Update / ❌ Delete")
    tid = st.number_input("Ticket ID", 1)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Update Ticket"):
            requests.put(
            f"{API_URL}/update_ticket/{tid}",
            headers=api_headers(),
            json={"status": "Closed"}
)

            st.success("Updated")
            st.rerun()

    with col2:
        if st.button("Delete Ticket"):
            requests.delete(
                f"{API_URL}/delete_ticket/{tid}",
                headers=api_headers()
            )
            st.success("Deleted")
            st.rerun()

# -----------------------
# Users (Admin only)
# -----------------------
def users_page():
    st.header("👤 User Management")

    email = st.text_input("Email")
    password = st.text_input("Password")
    role = st.selectbox("Role", ["staff", "admin"])

    if st.button("Create User"):
        res = requests.post(
            f"{API_URL}/users",
            headers=api_headers(),
            json={"email": email, "password": password, "role": role}
        )
        if res.status_code == 200:
            st.success("User created")

# -----------------------
# MAIN
# -----------------------
if "token" not in st.session_state:
    login_page()
else:
    st.sidebar.title("📌 Menu")

    menu = ["Dashboard", "Customers", "Tickets"]
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
    elif choice == "Logout":
        st.session_state.clear()
        st.rerun()
