from streamlit_menu.main_menu import API_URL,BACKEND_PORT,api_headers
import streamlit as st
import requests
from Redis.data_viewing import to_dataframe,hide_columns,select_columns,timing,rename_columns

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

