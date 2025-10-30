import streamlit as st
import requests

API_BASE = st.secrets.get("api_base", "http://localhost:8000")
api_base = https://codexedu.onrender.com

def do_login(email: str, password: str):
    resp = requests.post(f"{API_BASE}/auth/login", json={"email": email, "password": password})
    if resp.status_code == 200:
        token = resp.json().get("access_token")
        st.session_state["token"] = token
        # Clear old state on login
        for key in ["last_report", "current_exam_id", "current_exam", "questions", "answers"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state["is_logged_in"] = True
        st.success("Logged in successfully")
        st.switch_page("pages/dashboard.py")
    else:
        try:
            detail = resp.json().get("detail", "Login failed")
        except Exception:
            detail = f"Login failed ({resp.status_code})"
        st.error(detail)


def do_register(name: str, email: str, password: str):
    resp = requests.post(
        f"{API_BASE}/auth/register", json={"name": name, "email": email, "password": password}
    )
    if resp.status_code == 200:
        token = resp.json().get("access_token")
        st.session_state["token"] = token
        # Clear old state on register
        for key in ["last_report", "current_exam_id", "current_exam", "questions", "answers"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state["is_logged_in"] = True
        st.success("Registered and logged in")
        st.switch_page("pages/dashboard.py")
    else:
        try:
            detail = resp.json().get("detail", "Registration failed")
        except Exception:
            detail = f"Registration failed ({resp.status_code})"
        st.error(detail)


st.title("🔐 Login / Register")

if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False

if st.session_state["is_logged_in"]:
    st.info("You are already logged in.")
    st.page_link("pages/dashboard.py", label="Go to Dashboard", icon="📊")
else:
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                do_login(email, password)

    with tab2:
        with st.form("register_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Register")
            if submitted:
                do_register(name, email, password)


