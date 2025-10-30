from typing import List, Dict, Any
import os
import json

try:
    import tomllib  # py311+
except Exception:  # pragma: no cover
    tomllib = None

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
LOG_PATH = os.path.join(DATA_DIR, "ai_logs.log")


def _log_ai(message: str) -> None:
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception:
        pass


def _load_openai_api_key() -> str | None:
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    if tomllib is not None:
        secrets_path = os.path.join(BASE_DIR, ".streamlit", "secrets.toml")
        if os.path.exists(secrets_path):
            try:
                with open(secrets_path, "rb") as f:
                    data = tomllib.load(f)
                return data.get("openai_api_key") or data.get("OPENAI_API_KEY")
            except Exception:
                return None
    return None


def analyze_performance(questions: List[Dict[str, Any]], answers: Dict[str, str]) -> Dict[str, Any]:
    total = len(questions)
    correct = 0
    topic_totals: Dict[str, int] = {}
    topic_correct: Dict[str, int] = {}
    question_feedback = []
    for q in questions:
        qid = q["id"]
        topic = q.get("topic", "General")
        options_dict = q.get("options") or {}
        student_ans = answers.get(qid, "?")
        correct_label = q.get("answer")
        selected_text = options_dict.get(student_ans, "")
        correct_text = options_dict.get(correct_label, "")
        is_corr = student_ans == correct_label
        question_feedback.append({
            "question": q.get("question"),
            "topic": topic,
            "selected_label": student_ans,
            "selected_text": selected_text,
            "correct_label": correct_label,
            "correct_text": correct_text,
            "is_correct": is_corr
        })
        topic_totals[topic] = topic_totals.get(topic, 0) + 1
        if is_corr:
            correct += 1
            topic_correct[topic] = topic_correct.get(topic, 0) + 1
    overall_accuracy = round((correct / total) * 100, 2) if total else 0.0
    topic_accuracy: Dict[str, float] = {}
    for topic, t_total in topic_totals.items():
        t_correct = topic_correct.get(topic, 0)
        topic_accuracy[topic] = round((t_correct / t_total) * 100, 2)
    # Retain LLM/rule feedback as separate key for backward-compat.
    overall_feedback = ""
    api_key = _load_openai_api_key()
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            system = (
                "You are a helpful math coach. Summarize student performance in 2-3 sentences: "
                "mention strong topics, weak topics, and give encouraging next steps. Keep it concise and motivational."
            )
            payload = {
                "overall_accuracy": overall_accuracy,
                "topic_accuracy": topic_accuracy,
            }
            _log_ai(f"[feedback][request] {json.dumps(payload, ensure_ascii=False)}")
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_FEEDBACK_MODEL", os.getenv("OPENAI_MATH_MODEL", "gpt-4o-mini")),
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                temperature=0.7,
                max_tokens=200,
            )
            overall_feedback = resp.choices[0].message.content.strip()
            _log_ai(f"[feedback][response] {overall_feedback}")
        except Exception as e:
            overall_feedback = None
    if not overall_feedback:
        strengths = [t for t, acc in topic_accuracy.items() if acc >= 70]
        weaknesses = [t for t, acc in topic_accuracy.items() if acc < 50]
        feedback_parts = []
        if strengths:
            feedback_parts.append(f"Strong in: {', '.join(strengths)}.")
        if weaknesses:
            feedback_parts.append(f"Needs practice: {', '.join(weaknesses)}.")
        if not feedback_parts:
            feedback_parts.append("Balanced performance. Keep practicing!")
        overall_feedback = " ".join(feedback_parts)
    return {
        "overall_accuracy": overall_accuracy,
        "topic_accuracy": topic_accuracy,
        "overall_feedback": overall_feedback,
        "feedback": question_feedback
    }


