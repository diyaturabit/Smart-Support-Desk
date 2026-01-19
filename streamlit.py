import streamlit as st
import requests
from Redis.data_viewing import to_dataframe,hide_columns,select_columns,timing,rename_columns
API_URL = "http://127.0.0.1:5000"

st.set_page_config("Smart Support Desk", layout="wide")
st.markdown("""
<style>
/* Remove Streamlit default padding */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 1rem;
}

/* Metric cards */
[data-testid="metric-container"] {
    background-color: #0f172a;
    padding: 18px;
    border-radius: 12px;
    color: white;
}

/* Section headers */
.section {
    padding: 1rem;
    border-radius: 12px;
    background-color: #020617;
    margin-bottom: 1rem;
}

/* Table container */
.stDataFrame {
    border-radius: 12px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #E6E6FA;
}
</style>
""", unsafe_allow_html=True)

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
    st.title("📊 Admin Overview")

    # ---- METRICS ----
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("👥 Customers", stats["total_customer"])
    col2.metric("📂 Open", stats["open"])
    col3.metric("🔥 High", stats["high"])
    col4.metric("⚡ Medium", stats["medium"])
    col5.metric("🟢 Low", stats["low"])

    st.divider()

    # ---- TABS ----
    tab1, tab2,tab3,tab4 = st.tabs(["📈 Customer Summary", "🧾 Activity Logs","Assigning Tickets","Search"])

    # ---- CUSTOMER SUMMARY ----
    with tab1:
        st.subheader("Customers & Tickets")

        customer_ticket = stats.get("customer_ticket", [])
        if customer_ticket:
            df = to_dataframe(customer_ticket)
            df = rename_columns(df, {
                "name": "Customer",
                "email": "Email",
                "staff_email": "Created By",
                "ticket_count": "Tickets"
            })
            df.index += 1
            st.dataframe(df, use_container_width=True, height=350)
        else:
            st.info("No customer data available")

    # ---- ACTIVITY LOGS ----
    with tab2:
        st.subheader("Recent Activity")

        res = requests.get(f"{API_URL}/activity_logs", headers=api_headers())
        if res.status_code == 200:
            logs = res.json()["logs"]
            df = to_dataframe(logs)
            df = rename_columns(df, {
                "user_email": "User",
                "role": "Role",
                "action": "Action",
                "description": "Details",
                "created_at": "Time"
            })
            df = hide_columns(df, ["entity"])
            df = timing(df, "Time")
            df.index += 1
            st.dataframe(df, use_container_width=True, height=350)
        else:
            st.error("Failed to load logs")

    with tab3:
        st.subheader("Assigning Tickets")
        
        res=requests.get(f"{API_URL}/dashboard",headers=api_headers(),params={"assigned":"false"})
        unassigned=res.json()["unassigned_ticket"]
        ticket_map = {f'{u["id"]} ({u["title"]})': u for u in unassigned}
        selected = st.selectbox("Select Ticket", [""] + list(ticket_map.keys()))
        if not selected:
            st.warning("Please select a ticket")
            return 
        ticket=ticket_map[selected]
        user_ticket_count = res.json().get("user_ticket_count", [])
        count_map = {u["user_id"]: u["ticket_count"] for u in user_ticket_count}
        sta=requests.get(f"{API_URL}/get_user",headers=api_headers())
        staff=sta.json()["users"]
        staff_map = {
    f'{s["email"]} ({count_map.get(s["id"], 0)} tickets)': s
    for s in staff
}
        staff_select=st.selectbox("Select Staff",[""]+ list(staff_map.keys()))
        if not staff_select:
            st.warning("Please select an Staff for assign ticket")
            return
        agent_id=staff_map[staff_select]["id"]

        if st.button("Assign Ticket"):
            res = requests.put(
            f"{API_URL}/tickets/{ticket['id']}/assign",
            headers=api_headers(),
            json={"agent_id": agent_id}
    )
            if res.status_code == 200:
                st.success("Ticket assigned successfully")
                st.rerun()

    with tab4:
        st.subheader("🔍 Search")

        query = st.text_input(
            "Search customers or tickets",
            placeholder="Name, email, ticket title..."
        )

        if query:
            res = requests.get(
                f"{API_URL}/search",
                headers=api_headers(),
                params={"q": query}
            )

            if res.status_code == 200:
                data = res.json()

                customers = data.get("customers", [])
                tickets = data.get("tickets", [])

                if customers:
                    st.markdown("### 👥 Customers")
                    df_customers = to_dataframe(customers)
                    df_customers = hide_columns(df_customers, ["id"])
                    df_customers.index += 1
                    st.dataframe(df_customers, use_container_width=True)
                else:
                    st.info("No customers found")

        
                if tickets:
                    st.markdown("### 🎟️ Tickets")
                    df_tickets = to_dataframe(tickets)
                    df_tickets = hide_columns(
                        df_tickets, ["id", "customer_id"]
                    )
                    df_tickets.index += 1
                    st.dataframe(df_tickets, use_container_width=True)
                else:
                    st.info("No tickets found")

            else:
                st.error("Search failed")







def staff_dashboard(stats):
    st.header("👨‍💻 Staff Dashboard")

    c1, c2,c3,c4 = st.columns(4)
    c1.metric("📂 Open Tickets", stats["open"])
    c2.metric("🔥 High Priority Tickets", stats["high"])
    c3.metric("🔥 Low Priority Tickets", stats["low"])
    c4.metric("Assigned Ticket",stats["assigned_count"])


    st.success("Focus on resolving open and high-priority tickets")


# -----------------------
# Customers
# -----------------------
def customers_page():
    st.title("👥 Customers")

    tab1, tab2, tab3 = st.tabs(["➕ Create", "✏️ Update / Delete", "📋 View All"])

    # -------- CREATE --------
    with tab1:
        st.subheader("Create New Customer")

        with st.container(border=True):
            c_name = st.text_input("Name")
            c_email = st.text_input("Email")
            c_company = st.text_input("Company")
            c_age = st.number_input("Age", min_value=1)

            if st.button("Create Customer", use_container_width=True):
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

    # -------- UPDATE / DELETE --------
    with tab2:
        st.subheader("Update or Delete Customer")

        res = requests.get(f"{API_URL}/get_customer", headers=api_headers())
        customers = res.json()["customers"]

        cust_map = {f'{c["name"]} ({c["email"]})': c for c in customers}
        selected = st.selectbox("Select Customer", [""] + list(cust_map.keys()))

        if selected:
            c = cust_map[selected]

            name = st.text_input("Name", c["name"])
            email = st.text_input("Email", c["email"])
            company = st.text_input("Company", c["company"])
            age = st.number_input("Age", min_value=1, value=c["age"])

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Update", use_container_width=True):
                    res = requests.put(
                        f"{API_URL}/update_customer/{c['id']}",
                        headers=api_headers(),
                        json={
                            "name": name,
                            "email": email,
                            "company": company,
                            "age": age
                        }
                    )
                    st.success("Updated")
                    st.rerun()

            with col2:
                if st.button("Delete", use_container_width=True):
                    st.warning("Customer deleted")
                    requests.delete(
                        f"{API_URL}/delete_customer/{c['id']}",
                        headers=api_headers()
                    )
                    st.rerun()

    # -------- VIEW --------
    with tab3:
        st.subheader("All Customers")

        res = requests.get(f"{API_URL}/get_customer", headers=api_headers())
        customers = res.json()["customers"]

        df = to_dataframe(customers)
        df = hide_columns(df, ["id"])
        df.index += 1
        st.dataframe(df, use_container_width=True, height=450)


# ----------------- MAIN PAGE -----------------
def tickets_page():
    st.header("🎟️ Tickets Management")

    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Create",
        "✏️ Update / Delete",
        "📋 View Tickets",
        "🧑‍💻 Assigned To Me"
    ])

    # =====================================================
    # TAB 1 : CREATE TICKET
    # =====================================================
    with tab1:
        st.subheader("➕ Create Ticket")

        cust_res = requests.get(f"{API_URL}/get_customer", headers=api_headers())
        customers = cust_res.json().get("customers", [])

        if not customers:
            st.warning("No customers found")
            return

        emails = [c["email"] for c in customers]
        email = st.selectbox("Customer Email", [""] + emails)

        title = st.text_input("Title")
        description = st.text_area("Description")
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])

        if st.button("Create Ticket"):
            if not email or not title:
                st.warning("Email and Title are required")
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
                st.success("Ticket created successfully")
                st.rerun()
            else:
                st.error(res.text)

    # =====================================================
    # TAB 2 : UPDATE / DELETE
    # =====================================================
    with tab2:
        st.subheader("✏️ Update / Delete Ticket")

        role = st.session_state.get("role")

        cust_res = requests.get(f"{API_URL}/get_customer", headers=api_headers())
        data = cust_res.json()

        if role == "staff":
            customers = data.get("ticket_entry", [])
        elif role == "admin":
            customers = data.get("admin_ticket", [])
        else:
            st.error("Invalid role")
            return

        cust_map = {f"{c['name']} ({c['email']})": c for c in customers}

        customer_key = st.selectbox("Customer", [""] + list(cust_map.keys()))

        if not customer_key:
            st.stop()

        customer_id = cust_map[customer_key]["id"]

        ticket_res = requests.get(
            f"{API_URL}/customer/{customer_id}/tickets",
            headers=api_headers()
        )

        tickets = ticket_res.json().get("tickets", [])

        if not tickets:
            st.warning("No tickets found")
            st.stop()

        ticket_map = {f"{t['id']} - {t['title']}": t for t in tickets}
        selected = st.selectbox("Select Ticket", list(ticket_map.keys()))

        t = ticket_map[selected]

        title = st.text_input("Title", t["title"])
        description = st.text_area("Description", t["description"])
        priority = st.selectbox(
            "Priority",
            ["High", "Medium", "Low"],
            index=["High", "Medium", "Low"].index(t["priority"])
        )

        payload = {
            "title": title,
            "description": description,
            "priority": priority
        }

        if role == "admin":
            status = st.selectbox(
                "Status",
                ["Open", "Inprogress", "Closed"],
                index=["Open", "Inprogress", "Closed"].index(t["status"])
            )
            payload["status"] = status
            
       
    
       # Close ticket button (staff/admin)
        if st.button("Close Ticket", key=f"close_{t['id']}"):
            close_payload = {"status": "Closed"}
            res = requests.put(
                f"{API_URL}/update_ticket/{t['id']}",
                headers=api_headers(),
                json=close_payload
            )
            if res.status_code == 200:
                st.success("Ticket closed successfully")
                st.rerun()
            else:
                st.error(res.json().get("error", res.text))

        # Update ticket button (updates other fields + status if admin)
        if st.button("Update Ticket",key=f"update_{t['id']}"):
            res = requests.put(
                f"{API_URL}/update_ticket/{t['id']}",
                headers=api_headers(),
                json=payload
            )
            if res.status_code == 200:
                st.success("Ticket updated")
                st.rerun()
            else:
                st.error(res.json().get("error", res.text))

        st.info(f"Current Status: {t['status']}")

        if st.button("Delete Ticket",key=f"delete_{t['id']}"):
            res = requests.delete(
                f"{API_URL}/delete_ticket/{t['id']}",
                headers=api_headers()
            )

            if res.status_code == 200:
                st.success("Ticket deleted")
                st.rerun()
            else:
                st.error(res.text)
        print("Hello")
        
            
    # =====================================================
    # TAB 3 : VIEW ALL TICKETS
    # =====================================================
    with tab3:
        st.subheader("📋 View Tickets")
        
        col1, col2 = st.columns(2)
        with col1:
            status = st.selectbox("Status", ["All", "Open", "Inprogress", "Closed"])
        with col2:
            priority = st.selectbox("Priority", ["All", "High", "Medium", "Low"])

       
        res = requests.get(
            f"{API_URL}/tickets",
            headers=api_headers(),
            params={
                "mode": "all",
                "status": status if status != "All" else None,
                "priority": priority if priority != "All" else None
            }
        )
        if res.status_code != 200:
            st.error("Failed to load tickets")
            return

        tickets = res.json().get("tickets", [])
        df = to_dataframe(tickets)

        if df.empty:
            st.info("No tickets found")
        else:
            df = hide_columns(df, ["id", "customer_id", "assigned_to"])
            df.index += 1
            st.dataframe(df, use_container_width=True)

        
       

    with tab4:
        st.subheader("🧑‍💻 Tickets Assigned To Me")

        res = requests.get(
            f"{API_URL}/tickets",
            headers=api_headers(),
            params={"mode": "assigned"}
        )

        if res.status_code != 200:
            st.error("Failed to load assigned tickets")
            return

        assigned = res.json().get("assigned_to_user", [])
        df = to_dataframe(assigned)

        if df.empty:
            st.info("No tickets assigned to you")
        else:
            df = hide_columns(df, ["id", "customer_id", "assigned_to"])
            df.index += 1
            st.dataframe(df, use_container_width=True)

    
        


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

    



if "token" not in st.session_state:
    login_page()
else:
    st.sidebar.markdown("## 🧠 Smart Support Desk")
    st.sidebar.caption(f"Role: {st.session_state['role'].upper()}")
    st.sidebar.divider()


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
