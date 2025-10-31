import streamlit as st
import requests

API_BASE = st.secrets.get("api_base", "https://codexedu.onrender.com")



def auth_headers():
    token = st.session_state.get("token")
    if not token:
        st.warning("Please login first.")
        st.stop()
    return {"Authorization": f"Bearer {token}"}


st.title("📝 Take Exam")

# Mode and difficulty controls
mode = st.selectbox(
    "Generation mode",
    options=["deterministic", "ai", "ai_adaptive"],
    index=1,
    help="Use AI if available; ai_adaptive focuses on weak topics",
)
difficulty = st.selectbox(
    "Difficulty",
    options=["easy", "medium", "hard"],
    index=1,
)
num_questions = st.slider("Number of questions", min_value=5, max_value=20, value=10, step=1)

headers = auth_headers()

if "current_exam" not in st.session_state:
    st.session_state["current_exam"] = None

if st.button("Generate Exam"):
    payload = {"mode": mode, "difficulty": difficulty, "num_questions": num_questions}
    resp = requests.post(f"{API_BASE}/exam/generate", json=payload, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        if "exam_id" not in data:
            st.session_state["current_exam"] = None
            st.session_state["current_exam_id"] = None
            st.error("No valid exam_id returned from the backend.")
        else:
            st.session_state["current_exam"] = data
            st.session_state["current_exam_id"] = data.get("exam_id")
            if data.get("mode") == "ai":
                st.success("🤖 AI Mode Active")
    else:
        st.error("Failed to generate exam")

exam = st.session_state["current_exam"]
if exam:
    exam_id = st.session_state.get("current_exam_id")
    questions = exam.get("questions", [])
    answers = {}
    st.write(f"Exam ID: {exam_id}")
    if exam.get("mode") == "ai":
        st.caption("🤖 AI Mode Active")
    for q in questions:
        st.markdown(f"**{q['question']}**  ")
        key = f"ans_{q['id']}"
        choice = st.radio("Select one:", options=list(q["options"].keys()), format_func=lambda x: f"{x}) {q['options'][x]}", key=key)
        answers[q["id"]] = choice
        st.divider()

    if st.button("Submit Exam"):
        payload = {
            "exam_id": exam_id,
            "questions": questions,
            "answers": answers
        }
        resp = requests.post(
            f"{API_BASE}/exam/submit",
            headers=headers,
            json=payload,
        )
        if resp.status_code == 200:
            st.session_state["last_report"] = resp.json()
            st.success("Exam submitted. View your report.")
            st.switch_page("pages/report.py")
        else:
            try:
                msg = resp.json().get("detail", "Submission failed")
            except Exception:
                msg = "Submission failed"
            st.error(msg)


