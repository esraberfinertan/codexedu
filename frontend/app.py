import streamlit as st

st.set_page_config(page_title="CodexEDU", page_icon="🎓", layout="wide")

st.title("CodexEDU 🎓")
st.write("AI-powered educational platform for personalized math learning.")

st.page_link("pages/login.py", label="Login / Register", icon="🔐")
st.page_link("pages/dashboard.py", label="Dashboard", icon="📊")
st.page_link("pages/exam.py", label="Take Exam", icon="📝")
st.page_link("pages/report.py", label="Reports", icon="🧠")

st.divider()
st.markdown("Use the sidebar to navigate between pages.")


