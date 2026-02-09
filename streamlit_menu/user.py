from streamlit_menu.main_menu import API_URL,BACKEND_PORT,api_headers
import streamlit as st
import requests
from Redis.data_viewing import to_dataframe,hide_columns,select_columns,timing,rename_columns


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