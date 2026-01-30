import streamlit as st
import requests
from Redis.data_viewing import to_dataframe,hide_columns,select_columns,timing,rename_columns
API_URL = "http://192.168.1.70:5000"
BACKEND_PORT="http://192.168.1.70:8000"
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
    res = requests.post(f"{API_URL}/auth/login", json={
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
    res = requests.get(f"{API_URL}/dashboard/dashboard", headers=api_headers())

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

        res = requests.get(f"{API_URL}/logs/activity_logs", headers=api_headers())
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
        st.subheader("🎯 Assigning Tickets")

        res = requests.get(
            f"{API_URL}/dashboard/dashboard",
            headers=api_headers(),
            params={"assigned": "false"}
        )

        unassigned = res.json().get("unassigned_ticket", [])
        user_ticket_count = res.json().get("user_ticket_count", [])

        ticket_map = {f'{u["id"]} - {u["title"]}': u for u in unassigned}

        selected_ticket_key = st.selectbox(
            "🎟️ Select Ticket",
            [""] + list(ticket_map.keys()),
            key="assign_ticket_select"
        )

        ticket = ticket_map.get(selected_ticket_key)


        count_map = {u["user_id"]: u["ticket_count"] for u in user_ticket_count}

        sta = requests.get(f"{API_URL}/auth/get_user", headers=api_headers())
        staff = sta.json().get("users", [])

        staff_map = {
            f'{s["email"]} ({count_map.get(s["id"], 0)} tickets)': s
            for s in staff
        }

        selected_staff_key = st.selectbox(
            "👤 Select Staff",
            [""] + list(staff_map.keys()),
            key="assign_staff_select"
        )

        agent = staff_map.get(selected_staff_key)

        assign_disabled = not ticket or not agent

        if st.button("✅ Assign Ticket", disabled=assign_disabled):
            res = requests.put(
                f"{API_URL}/ticket/tickets/{ticket['id']}/assign",
                headers=api_headers(),
                json={"agent_id": agent["id"]}
            )

            if res.status_code == 200:
                st.success("Ticket assigned successfully 🎉")
                st.rerun()
            else:
                st.error(res.text)

        if not ticket:
            st.info("Select a ticket to continue")

        if not agent:
            st.info("Select a staff member to assign the ticket")

    with tab4:
        search_page()
        








def staff_dashboard(stats):
    st.header("👨‍💻 Staff Dashboard")

    c1, c2,c3,c4 = st.columns(4)
    c1.metric("📂 Open Tickets", stats["open"])
    c2.metric("🔥 High Priority Tickets", stats["high"])
    c3.metric("🔥 Low Priority Tickets", stats["low"])
    c4.metric("Assigned Ticket",stats["assigned_count"])


    st.success("Focus on resolving open and high-priority tickets")



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
                # res=requests.post(
                #     f"{BACKEND_PORT}/sync_customers/create_customers",json={
                #                  "name": c_name,
                #         "email": c_email,
                #         "company": c_company,
                #         "age": c_age
                #     }   
                # )
                # hubspot_id=res.json().get("hubspot_id")
                res = requests.post(
                    f"{API_URL}/customer/create_customer",
                    headers=api_headers(),
                    json={
                        "name": c_name,
                        "email": c_email,
                        "company": c_company,
                        "age": c_age
                    } 
                )
                data = res.json()
                customer_id = data.get("customer_id") or data.get("id")

                if not customer_id:
                    st.error(f"Customer created but ID not returned: {data}")
                    st.stop()

                requests.post(f"{BACKEND_PORT}/sync_customers/by-id",
                              json={"customer_id":customer_id})
                st.success("🚀 Customer synced to HubSpot")

                if res.status_code == 201:
                    # hubspot_id=res.json().get("hubspot_id")
                    st.success("Customer created in hubspot")
                    # st.session_state["hubspot_customer_id"] = hubspot_id
                else:
                    st.error("❌ Failed to create customer")
                    st.rerun()


    with tab2:
        st.subheader("Update or Delete Customer")

        res = requests.get(f"{API_URL}/customer/get_customer", headers=api_headers())
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
                    requests.put(f"{BACKEND_PORT}/sync_customers/update_customer",
                                  json={
                            "customer_id": c["id"],
                            "name": name,
                            "email": email,
                            "company": company,
                            "age": age
                        })
                    st.success("🚀 Ticket synced to HubSpot")
                    # res = requests.put(
                    #     f"{API_URL}/customer/update_customer/{c['id']}",
                    #     headers=api_headers(),
                    #     json={
                    #         "name": name,
                    #         "email": email,
                    #         "company": company,
                    #         "age": age
                    #     }
                    # )
                    st.success("Updated")
                    st.rerun()

            with col2:
                if st.button("Delete", use_container_width=True):
                    st.warning("Customer deleted")
                    requests.delete(f"{BACKEND_PORT}/sync_customers/delete_customer",
                                  json={"customer_id":c["id"]})
                    st.success("🚀 Ticket synced to HubSpot")
                    requests.delete(
                        f"{API_URL}/customer/delete_customer/{c['id']}",
                        headers=api_headers()
                    )
                    requests.delete(f"{BACKEND_PORT}/sync_customers/delete_customer",
                                  json={"customer_id":c["id"]})
                    st.success("🚀 Ticket synced to HubSpot")
                    st.rerun()

    # -------- VIEW --------
    with tab3:
        st.subheader("All Customers")

        res = requests.get(f"{API_URL}/customer/get_customer", headers=api_headers())
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


    with tab1:
        st.subheader("➕ Create Ticket")

        cust_res = requests.get(f"{API_URL}/customer/get_customer", headers=api_headers())
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
                f"{API_URL}/ticket/create_ticket",
                headers=api_headers(),
                json={
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "customer_id": customer_id
                }
            )
            ticket_id = res.json()["ticket_id"]
            requests.post(f"{BACKEND_PORT}/sync_tickets/id-by",
                          json={"ticket_id":ticket_id})
            st.success("🚀 Ticket synced to HubSpot")

            if res.status_code == 201:
                st.success("Ticket created successfully")
                st.rerun()
            else:
                st.error(res.text)

    
    with tab2:
       st.subheader("✏️ Update / Delete Ticket")

       role = st.session_state.get("role")

       cust_res = requests.get(f"{API_URL}/customer/get_customer", headers=api_headers())
       data = cust_res.json()

       if role == "staff":
           customers = data.get("ticket_entry", [])
       elif role == "admin":
           customers = data.get("admin_ticket", [])
       else:
           st.error("Invalid role")
           customers = []

       cust_map = {f"{c['name']} ({c['email']})": c for c in customers}
       customer_key = st.selectbox("Customer", [""] + list(cust_map.keys()))

       if customer_key:
           customer_id = cust_map[customer_key]["id"]

           ticket_res = requests.get(
               f"{API_URL}/customer/customer/{customer_id}/tickets",
               headers=api_headers()
           )

           tickets = ticket_res.json().get("tickets", [])

           if tickets:
               ticket_map = {f"{t['id']} - {t['title']}": t for t in tickets}
               selected = st.selectbox("Select Ticket", list(ticket_map.keys()))

               t = ticket_map[selected]

               title = st.text_input("Title", t["title"])
               description = st.text_area("Description", t["description"])
               priority = st.selectbox(
                   "Priority",
                   ["High", "Medium", "Low"],
                   index=["High", "Medium", "Low"].index(t["priority"]),key=f"priority_{t['id']}"
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
                       index=["Open", "Inprogress", "Closed"].index(t["status"]), key=f"status_{t['id']}"
                   )
                   payload["status"] = status

               col1, col2, col3 = st.columns(3)

               with col1:
                    if st.button("Update Ticket", key=f"update_{t['id']}"):
                    
                        sync_payload = {
                            "ticket_id": t["id"],
                            "title": title,
                            "description": description,
                            "priority": priority
                        }

                        if role == "admin":
                            sync_payload["status"] = status

                        res = requests.put(
                            f"{BACKEND_PORT}/sync_tickets/update_ticket",
                            json=sync_payload
                        )

                        if res.status_code == 200:
                            st.success("🚀 Ticket updated & synced to HubSpot")
                            st.rerun()
                        else:
                            st.error("Failed to update ticket")

 
               with col2:
                   if st.button("Close Ticket", key=f"close_{t['id']}"):
                       res = requests.put(
                           f"{API_URL}/ticket/update_ticket/{t['id']}",
                           headers=api_headers(),
                           json={"status": "Closed"}
                       )
                       if res.status_code == 200:
                           st.success("Ticket closed")
                           st.rerun()

               with col3:
                   if st.button("Delete Ticket", key=f"delete_{t['id']}"):
                       requests.delete(f"{BACKEND_PORT}/sync_tickets/ticket_delete",
                                  json={"ticket_id":t["id"]})
                       st.success("🚀 Ticket synced to HubSpot")
                       res = requests.delete(
                           f"{API_URL}/ticket/delete_ticket/{t['id']}",
                           headers=api_headers()
                       )
                       if res.status_code == 200:
                           st.success("Ticket deleted")
                           st.rerun()

               st.info(f"Current Status: {t['status']}")

           else:
               st.warning("No tickets found")
       else:
           st.info("Please select a customer to continue")

    with tab3:
        st.subheader("📋 View Tickets")
        
        col1, col2 = st.columns(2)
        with col1:
            status = st.selectbox("Status", ["All", "Open", "Inprogress", "Closed"])
        with col2:
            priority = st.selectbox("Priority", ["All", "High", "Medium", "Low"])

       
        res = requests.get(
            f"{API_URL}/ticket/tickets",
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
            f"{API_URL}/ticket/tickets",
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

    
        
def users_page():
    st.header("👤 User Management")

    email = st.text_input("Email")
    password = st.text_input("Password")
    role = st.selectbox("Role", ["staff", "admin"])

    if st.button("Create User"):
        res = requests.post(
            f"{API_URL}/auth/users",
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
            f"{API_URL}/auth/delete_user/{tid}",
            headers=api_headers(),
            )

            st.success("User Deleted")
            st.rerun()

    with col2:
        if st.button("View Users"):
            res = requests.get(
                f"{API_URL}/auth/get_user",
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
def search_page():
    st.subheader("🔍 Search")

    query = st.text_input(
        "Search customers or tickets",
        placeholder="Name, email, ticket title..."
    )

    if not query:
        st.info("Start typing to search customers or tickets")
        return

    res = requests.get(
        f"{API_URL}/search/search",
        headers=api_headers(),
        params={"q": query}
    )

    if res.status_code != 200:
        st.error("Search failed")
        return

    data = res.json()
    customers = data.get("customers", [])
    tickets = data.get("tickets", [])

    # ==================== CUSTOMERS ====================
    st.markdown("## 👥 Customers")

    selected_customer = None

    if not customers:
        st.info("No customers found")

    elif len(customers) == 1:
        # Auto select single customer
        selected_customer = customers[0]

    else:
        # Let user choose only if multiple
        selected_customer = st.radio(
            "Select a customer",
            customers,
            format_func=lambda c: f"{c['name']} ({c['email']})"
        )

    # -------------------- CUSTOMER DETAILS --------------------
    if selected_customer:
        customer_id = selected_customer["id"]

        detail_res = requests.get(
            f"{API_URL}/customer/customers/{customer_id}",
            headers=api_headers()
        )

        if detail_res.status_code == 200:
            detail = detail_res.json()

            customer = detail["customer"]
            tickets = detail["tickets"]
            ticket_count = detail["ticket_count"]

            st.markdown("---")
            st.markdown("## 🧾 Customer Overview")

            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"""
                <div style="
                    background:#E6E6FA;
                    padding:20px;
                    border-radius:16px;
                    color:black;
                ">
                    <h3 style="margin-bottom:8px;">👤 {customer['name']}</h3>
                    <p>📧 {customer['email']}</p>
                    <p>🏢 {customer.get('company', '—')}</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div style="
                    background:#E6E6FA;
                    padding:20px;
                    border-radius:16px;
                    text-align:center;
                    color:black;
                ">
                    <h1 style="margin:0;">{ticket_count}</h1>
                    <p>Total Tickets</p>
                </div>
                """, unsafe_allow_html=True)

    # ==================== TICKETS ====================
    st.markdown("## 🎟️ Tickets")

    if not tickets:
        st.info("No tickets found")
        return

    # Ticket table
    df_tickets = to_dataframe(tickets)
    df_tickets = hide_columns(df_tickets, ["id", "customer_id"])
    df_tickets.index += 1
    st.dataframe(df_tickets, use_container_width=True)


    st.markdown("### 🔍 Ticket Details")

    for t in tickets:
        with st.expander(f"#{t['id']} · {t['title']} · {t['status']}"):
            st.markdown(f"""
            <div style="
                background:#0f172a;
                padding:16px;
                border-radius:14px;
                color:white;
            ">
                <p><b>Priority:</b> {t['priority']}</p>
                <p><b>Status:</b> {t['status']}</p>
                <p><b>Created:</b> {t.get('created_at','—')}</p>
                <p><b>Description:</b></p>
                <p>{t.get('description','—')}</p>
            </div>
            """, unsafe_allow_html=True)



if "token" not in st.session_state:
    login_page()
else:
    st.sidebar.markdown("## 🧠 Smart Support Desk")
    st.sidebar.caption(f"Role: {st.session_state['role'].upper()}")
    st.sidebar.divider()


    menu = ["Dashboard", "Customers", "Tickets","Search"]
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
