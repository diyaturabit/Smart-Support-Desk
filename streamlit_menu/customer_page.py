import streamlit as st
import requests
from streamlit_menu.config import API_URL,BACKEND_PORT,api_headers
from Redis.data_viewing import to_dataframe,hide_columns,select_columns,timing,rename_columns

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

