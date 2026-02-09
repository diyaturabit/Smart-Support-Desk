from streamlit_menu.main_menu import API_URL,BACKEND_PORT,api_headers
import streamlit as st
import requests
from Redis.data_viewing import to_dataframe,hide_columns,select_columns,timing,rename_columns

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

    