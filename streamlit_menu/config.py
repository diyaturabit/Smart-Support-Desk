API_URL = "http://192.168.1.70:5000"
BACKEND_PORT="http://192.168.1.70:8000"
import streamlit as st

def api_headers():
    if not st.session_state.get("token"):
        return {}
    return {
        "Authorization": f"Bearer {st.session_state['token']}"
    }
