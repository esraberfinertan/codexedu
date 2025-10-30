import streamlit as st
import pandas as pd
import altair as alt
import requests

API_BASE = st.secrets.get("api_base", "http://localhost:8000")

token = st.session_state.get("token")
if not token:
    st.switch_page("pages/login.py")

st.title("🧠 Performance Report")

if st.session_state.get("review_exam_id"):
    exam_id = st.session_state["review_exam_id"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_BASE}/exam/{exam_id}", headers=headers)
    if resp.status_code == 200:
        report = resp.json()
    else:
        st.error("Could not load that exam.")
        st.stop()
    del st.session_state["review_exam_id"]
else:
    report = st.session_state.get("last_report")
    if not report:
        st.info("No report available. Take an exam first.")
        st.stop()

st.metric("Overall Accuracy", f"{report.get('overall_accuracy', report.get('score', 0))}%")

topic_acc = report.get("topic_accuracy", {})
if topic_acc:
    df = pd.DataFrame({"topic": list(topic_acc.keys()), "accuracy": list(topic_acc.values())})
    chart = alt.Chart(df).mark_bar().encode(x="topic", y="accuracy").properties(height=300)
    st.altair_chart(chart, use_container_width=True)

if "overall_feedback" in report:
    st.subheader("AI Feedback")
    st.write(report["overall_feedback"])

# Per-question feedback (handle empty/missing safely)
fb_data = report.get("feedback")
if isinstance(fb_data, list) and fb_data:
    st.markdown("### Detailed Feedback")
    for fb in fb_data:
        if fb.get("is_correct"):
            st.success(f"✅ {fb['question']}")
        else:
            st.error(f"❌ {fb['question']}")
            st.write(f"Your answer: **{fb['selected_label']}** — {fb['selected_text']}")
            st.write(f"Correct answer: **{fb['correct_label']}** — {fb['correct_text']}")
        st.caption(f"Topic: {fb.get('topic', '-')}")
        st.divider()
    # Optional: feedback table
    if st.checkbox("Show full feedback table"):
        import pandas as pd
        show_cols = ["topic", "question", "selected_label", "selected_text", "correct_label", "correct_text", "is_correct"]
        df = pd.DataFrame(fb_data)[show_cols]
        st.dataframe(df)
else:
    st.info("No detailed feedback available for this exam.")


