import streamlit as st
import requests
from Redis.data_viewing import to_dataframe,hide_columns,select_columns,rename_columns
API_URL = "http://127.0.0.1:5000"

st.set_page_config("Smart Support Desk", layout="wide")

# -----------------------
# Helpers
# -----------------------
def api_headers():
    if not st.session_state.get("token"):
        return {}
    return {
        "Authorization": f"Bearer {st.session_state['token']}"
    }

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
            st.success("Login successful")
            st.rerun()

# ---------------------------
# Dashboard 
# ---------------------------
def general_dashboard(stats):
    st.subheader("📊 Overview")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Customers", stats["total_customer"])
    c2.metric("Open Tickets", stats["open"])
    c3.metric("High Priority", stats["high"])

    c4, c5 = st.columns(2)
    c4.metric("Medium Priority", stats["medium"])
    c5.metric("Low Priority", stats["low"])

    

def dashboard_page():
    res = requests.get(f"{API_URL}/dashboard", headers=api_headers())

    if res.status_code != 200:
        st.error("Failed to load dashboard")
        return

    stats = res.json()
    role = st.session_state.get("role")

    if role == "admin":
        admin_dashboard(stats)
    else:
        staff_dashboard(stats)

def admin_dashboard(stats):
    st.header("🧑‍💼 Admin Dashboard")

    # --- General stats ---
    c1, c2, c3 = st.columns(3)
    c1.metric("👥 Total Customers", stats["total_customer"])
    c2.metric("📂 Open Tickets", stats["open"])
    c3.metric("🔥 High Priority", stats["high"])

    c4, c5 = st.columns(2)
    c4.metric("⚡ Medium Priority", stats["medium"])
    c5.metric("🟢 Low Priority", stats["low"])

    st.divider()
    st.subheader("👥 Customers & Ticket Summary")

    # --- Table of customers and tickets ---
    customer_ticket = stats.get("customer_ticket", [])
    if customer_ticket:
        df = to_dataframe(customer_ticket)
        df = rename_columns(df, {
            "name": "Customer Name",
            "email": "Customer Email",
            "staff_email": "Registered By",
            "ticket_count": "No. of Tickets"
        })
        df.index += 1  # Start index from 1
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("No customer data available")


    st.subheader("🧾 Activity Logs")
    
    res = requests.get(f"{API_URL}/activity_logs", headers=api_headers())
    
    if res.status_code == 200:
        logs = res.json()["logs"]
    
        df = to_dataframe(logs)
        df = rename_columns(df, {
            "user_email": "User",
            "role": "Role",
            "action": "Action",
            "entity": "Entity",
            "description": "Details",
            "created_at": "Time"
        })
    
        df.index += 1
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.error("Failed to load activity logs")

    st.divider()
    st.info("Admin can view all customers, tickets, reports & analytics")


def staff_dashboard(stats):
    st.header("👨‍💻 Staff Dashboard")

    c1, c2,c3 = st.columns(3)
    c1.metric("📂 Open Tickets", stats["open"])
    c2.metric("🔥 High Priority Tickets", stats["high"])
    c3.metric("🔥 Low Priority Tickets", stats["low"])

    st.success("Focus on resolving open and high-priority tickets")


# -----------------------
# Customers
# -----------------------
def customers_page():
    st.header("👥 Customers")
    customer_map = {}  # initialize empty

    # ---------- CREATE ----------
    st.subheader("➕ Create Customer")
    c_name = st.text_input("Name", key="c_create_name")
    c_email = st.text_input("Email", key="c_create_email", placeholder="example@company.com")
    c_company = st.text_input("Company", key="c_create_company")
    c_age = st.number_input("Age", key="c_create_age", value=1, min_value=1)

    if st.button("Create Customer"):
        res = requests.post(
            f"{API_URL}/create_customer",
            headers=api_headers(),
            json={
                "name": c_name,
                "email": c_email,
                "company": c_company,
                "age": c_age
                
            }
        )
        if res.status_code == 201:
            st.success("Customer created")
            st.rerun()

    # ---------- SELECT ----------
    st.subheader("✏️ Update / ❌ Delete")

    res = requests.get(f"{API_URL}/get_customer", headers=api_headers())
    if res.status_code == 200:
        customers = res.json()["customers"]
        customer_map = {c["email"]: c for c in customers}
    else:
        st.error("Failed to fetch customers")
        return

    selected_email = st.selectbox(
        "Select Customer",
        options=[""] + list(customer_map.keys()),  # first option empty
        key="customer_select"
    )

    if selected_email:  # if a customer is selected
        c = customer_map[selected_email]

        name = st.text_input("Name", c["name"])
        email = st.text_input("Email", c["email"])
        company = st.text_input("Company", c["company"])
        age = st.number_input("Age", min_value=1, value=c["age"])

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Update Customer"):
                requests.put(
                    f"{API_URL}/update_customer/{c['id']}",
                    headers=api_headers(),
                    json={
                        "name": name,
                        "email": email,
                        "company": company,
                        "age": age
                    }
                )
                st.success("Customer updated")
                st.rerun()

        with col2:
            if st.button("Delete Customer"):
                requests.delete(
                    f"{API_URL}/delete_customer/{c['id']}",
                    headers=api_headers()
                )
                st.success("Customer deleted")
                st.rerun()

    # ---------- VIEW TABLE ----------
    if st.button("View Customers"):
        res = requests.get(f"{API_URL}/get_customer", headers=api_headers())
        if res.status_code == 200:
            customers = res.json()["customers"]
            df=to_dataframe(customers)
            df=hide_columns(df,["id"])
            prior=["name","email","company","age"]
            ordered=prior + [c for c in df.columns if c not in prior]
            df=df[ordered]
            df.index=df.index+1
            st.dataframe(df,use_container_width=True)
        else:
            st.error("Failed to fetch customers")

# -----------------------
# Tickets

def tickets_page():
    st.header("View Tickets")
    status = st.selectbox("Status", ["", "Open","InProgress","Closed"])
    priority = st.selectbox("Priority", ["", "High", "Medium", "Low"])
    # ================= VIEW =================
    if st.button("View Tickets"):
        params = {}
        if status: 
            params["status"] = status
        if priority:
            params["priority"] = priority
        res = requests.get(f"{API_URL}/tickets", headers=api_headers(),params=params)

        if res.status_code == 200:
            tickets = res.json()["tickets"]
            df=to_dataframe(tickets)
            df=hide_columns(df,["id","customer_id"])
            prior=["title","description","priority","status"]
            ordered=prior + [c for c in df.columns if c not in prior]
            df=df[ordered]
            df.index=df.index+1
            st.dataframe(df,use_container_width=True)
        else:
            st.error("Failed to load tickets")

    # ================= CREATE =================
    st.subheader("➕ Create Ticket")

    cust_res = requests.get(f"{API_URL}/get_customer", headers=api_headers())
    customers = cust_res.json()["customers"]

    emails = [c["email"] for c in customers]
    email = st.selectbox("Customer Email", [""] + emails)

    title = st.text_input("Title")
    description = st.text_area("Description")
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])

    if st.button("Create Ticket"):
        if not email:
            st.warning("Please select customer email")
            return

        customer_id = next(c["id"] for c in customers if c["email"] == email)

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

        if res.status_code == 201:
            st.success("Ticket created")
            st.rerun()

       # ================= UPDATE =================
    st.subheader("✏️ Update Ticket")

    # --- Select customer ---
    cust_res = requests.get(f"{API_URL}/get_customer", headers=api_headers())
    customers = cust_res.json()["customers"]
    cust_map = {c["email"]: c["id"] for c in customers}

    customer_email = st.selectbox(
        "Select Customer Email",
        [""] + list(cust_map.keys()),
        key="upd_customer"
    )

    if not customer_email:
        st.stop()

    customer_id = cust_map[customer_email]

    # --- Get tickets ---
    ticket_res = requests.get(
        f"{API_URL}/customer/{customer_id}/tickets",
        headers=api_headers()
    )

    tickets = ticket_res.json().get("customer_ticket", [])
    if not tickets:
        st.warning("No tickets found")
        st.stop()

    ticket_map = {f"{t['id']} - {t['title']}": t for t in tickets}

    selected_ticket = st.selectbox(
        "Select Ticket",
        list(ticket_map.keys()),
        key="upd_ticket"
    )

    t = ticket_map[selected_ticket]

    # --- EDIT FIELDS (OUTSIDE BUTTON!) ---
    title = st.text_input("Title", t["title"], key=f"upd_title{t['id']}")
    description = st.text_input("Description", t["description"], key=f"upd_desc{t['id']}")
    priority = st.selectbox(
        "Priority",
        ["High", "Medium", "Low"],
        index=["High", "Medium", "Low"].index(t["priority"]),
        key=f"upd_priority{t['id']}"
    )
    status = st.selectbox(
        "Status",
        ["Open", "Inprogress", "Closed"],
        index=["Open", "Inprogress", "Closed"].index(t["status"]),
        key=f"upd_status{t['id']}"
    )

    # --- UPDATE ---
    if st.button("Update Ticket"):
        res = requests.put(
            f"{API_URL}/update_ticket/{t['id']}",
            headers=api_headers(),
            json={
                "title": title,
                "description": description,
                "priority": priority,
                "status": status
            }
        )

        if res.status_code == 200:
            st.success("Ticket updated")
            st.rerun()
        else:
            st.error(res.text)


    if st.button("Delete Ticket"):
        res = requests.delete(
            f"{API_URL}/delete_ticket/{t['id']}",
            headers=api_headers()
        )
        if res.status_code == 200:
            st.success("Ticket deleted")
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
    st.subheader("✏️ Delete / View")
    tid = st.number_input("Enter User Id", 1)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Delete User"):
            requests.delete(
            f"{API_URL}/delete_user/{tid}",
            headers=api_headers(),
            )

            st.success("User Deleted")
            st.rerun()

    with col2:
        if st.button("View Users"):
            res = requests.get(
                f"{API_URL}/get_user",
                headers=api_headers()
            )

            if res.status_code == 200:
                users = res.json()["users"]
                st.subheader("👥 Users List")
                df=to_dataframe(users)
                df=hide_columns(df,["id"])
                df.index+=1
                st.dataframe(df,use_container_width=True)
            else:
                st.error("Failed to fetch users")

    


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
