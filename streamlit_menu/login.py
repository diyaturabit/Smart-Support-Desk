from streamlit_menu.config import api_headers
from streamlit_menu.config import API_URL,BACKEND_PORT
headers = api_headers()

import streamlit as st
import requests
from Redis.data_viewing import to_dataframe,hide_columns,select_columns,timing,rename_columns


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
