import streamlit as st
import requests
import pandas as pd
import altair as alt
import os
API_BASE = os.environ.get("API_BASE", "https://codexedu-api.onrender.com")


def auth_headers():
    token = st.session_state.get("token")
    if not token:
        st.session_state["is_logged_in"] = False
        st.warning("Please login first.")
        st.switch_page("pages/login.py")
    else:
        st.session_state["is_logged_in"] = True
    return {"Authorization": f"Bearer {token}"}


st.title("📊 Dashboard")

if "is_logged_in" not in st.session_state or not st.session_state["is_logged_in"]:
    st.switch_page("pages/login.py")

# Logout button in sidebar
if st.sidebar.button("Log out"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("You have been logged out.")
    st.switch_page("pages/login.py")

headers = auth_headers()

col1, col2 = st.columns(2)

with col1:
    st.subheader("My Recent Exams")
    resp = requests.get(f"{API_BASE}/exam/me", headers=headers)
    if resp.status_code == 200:
        exams = resp.json()
        if exams:
            df = pd.DataFrame(exams)
            st.dataframe(df[["id", "created_at", "score"]])
        else:
            st.info("No exams yet. Go take one!")
    else:
        st.error("Failed to fetch exams")

with col2:
    st.subheader("Overall Accuracy")
    if resp.status_code == 200 and resp.json():
        scores = [e.get("score", 0) for e in resp.json()]
        overall = round(sum(scores) / len(scores), 2) if scores else 0.0
        st.metric("Average Score", f"{overall}%")
    else:
        st.metric("Average Score", "0%")

# Show review section
if resp.status_code == 200 and resp.json():
    exams = resp.json()
    st.markdown("### Review Your Past Exams")
    for ex in exams:
        label = f"View Exam {ex['id']} (Score: {ex['score']}%)"
        if st.button(label, key=f"review_exam_{ex['id']}"):
            st.session_state["review_exam_id"] = ex["id"]
            st.switch_page("pages/report.py")

st.subheader("Topic-wise Performance (last exam)")
if resp.status_code == 200 and resp.json():
    last = resp.json()[0]
    topic_stats = last.get("topic_accuracy", {})
    if topic_stats:
        df_topics = pd.DataFrame({"topic": list(topic_stats.keys()), "accuracy": list(topic_stats.values())})
        chart = alt.Chart(df_topics).mark_bar().encode(x="topic", y="accuracy").properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No topic data yet.")

st.page_link("pages/exam.py", label="Take a new exam ➜", icon="📝")


