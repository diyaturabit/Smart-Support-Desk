from streamlit_menu.main_menu import API_URL,BACKEND_PORT,api_headers
import streamlit as st
import requests
from Redis.data_viewing import to_dataframe,hide_columns,select_columns,timing,rename_columns
from search import search_page


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
