from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
from datetime import datetime

from backend.auth import router as auth_router, decode_access_token
from backend.database import ExamsSession, Exam, init_databases
from backend.ai_engine.question_generator import generate_exam
from backend.ai_engine.report_analyzer import analyze_performance
from backend.ai_engine.dataset_builder import append_result_to_dataset



class GenerateExamRequest(BaseModel):
    topics: Optional[List[str]] = None
    mode: Optional[str] = "ai"  # deterministic | ai | ai_adaptive (AI default if available)
    difficulty: Optional[str] = "medium"    # easy | medium | hard
    num_questions: Optional[int] = 10


class SubmitExamRequest(BaseModel):
    exam_id: Optional[int] = None
    questions: List[Dict[str, Any]]
    answers: Dict[str, str]  # question_id -> selected_option (e.g., "A")


security = HTTPBearer()


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return int(payload.get("sub"))


def create_app() -> FastAPI:
    init_databases()
    app = FastAPI(title="CodexEDU API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="/auth", tags=["auth"]) 

    @app.get("/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok"}

    def _compute_weak_topics(user_id: int, default_topics: List[str]) -> List[str]:
        # Read ai_dataset.csv and compute average accuracy per topic for this user
        import csv
        import os
        data_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)), "data", "ai_dataset.csv")
        if not os.path.exists(data_path):
            return default_topics
        topic_scores: Dict[str, List[float]] = {}
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if str(row.get("user_id")) != str(user_id):
                        continue
                    topic = row.get("topic")
                    try:
                        acc = float(row.get("accuracy", 0))
                    except Exception:
                        acc = 0.0
                    topic_scores.setdefault(topic, []).append(acc)
        except Exception:
            return default_topics

        if not topic_scores:
            return default_topics
        # Average accuracy, sort ascending to prioritize weak topics
        avg = sorted(((t, sum(v)/len(v)) for t, v in topic_scores.items()), key=lambda x: x[1])
        # Take bottom half or at least 2 topics
        k = max(2, len(avg)//2)
        return [t for t, _ in avg[:k]]

    @app.post("/exam/generate")
    async def generate_exam_endpoint(body: GenerateExamRequest, user_id: int = Depends(get_current_user_id)):
        topics = body.topics or ["Algebra", "Functions", "Integrals", "Derivatives", "Geometry"]
        mode = (body.mode or "deterministic").lower()
        difficulty = (body.difficulty or "medium").lower()
        num_q = int(body.num_questions or 10)

        if mode == "ai_adaptive":
            topics = _compute_weak_topics(user_id=user_id, default_topics=topics)

        exam = generate_exam(
            topics=topics,
            num_questions=num_q,
            mode=mode,
            difficulty=difficulty,
            avoid_repeat=True,
        )

        session = ExamsSession()
        try:
            exam_row = Exam(
                user_id=user_id,
                created_at=datetime.utcnow(),
                questions_json=json.dumps(exam["questions"]),
                answers_json=json.dumps({}),
                score=0.0,
                topic_stats_json=json.dumps({}),
            )
            session.add(exam_row)
            session.commit()
            session.refresh(exam_row)
            exam_id = exam_row.id
        finally:
            session.close()

        return {"exam_id": exam_id, **exam}

    @app.post("/exam/submit")
    async def submit_exam_endpoint(body: SubmitExamRequest, user_id: int = Depends(get_current_user_id)):
        session = ExamsSession()
        try:
            if body.exam_id is None:
                # create ephemeral exam record if not provided
                exam_row = Exam(
                    user_id=user_id,
                    created_at=datetime.utcnow(),
                    questions_json=json.dumps(body.questions),
                    answers_json=json.dumps(body.answers),
                    score=0.0,
                    topic_stats_json=json.dumps({}),
                )
                session.add(exam_row)
                session.commit()
                session.refresh(exam_row)
            else:
                exam_row = session.query(Exam).filter(Exam.id == body.exam_id, Exam.user_id == user_id).first()
                if not exam_row:
                    raise HTTPException(status_code=404, detail="Exam not found for this user")
                exam_row.questions_json = json.dumps(body.questions)
                exam_row.answers_json = json.dumps(body.answers)

            questions = body.questions
            answers = body.answers
            analysis = analyze_performance(questions, answers)
            exam_row.score = float(analysis["overall_accuracy"])
            exam_row.topic_stats_json = json.dumps(analysis["topic_accuracy"])
            # Save feedback list (not just overall summary)
            if hasattr(exam_row, "feedback_json"):
                exam_row.feedback_json = json.dumps(analysis.get("feedback", []))
            session.commit()
            append_result_to_dataset(user_id=user_id, topic_accuracy=analysis["topic_accuracy"])
            return {
                "exam_id": exam_row.id,
                "overall_accuracy": analysis["overall_accuracy"],
                "topic_accuracy": analysis["topic_accuracy"],
                "feedback": analysis["feedback"],
                "overall_feedback": analysis.get("overall_feedback")
            }
        finally:
            session.close()

    @app.get("/exam/me")
    async def list_my_exams(user_id: int = Depends(get_current_user_id)):
        session = ExamsSession()
        try:
            rows = (
                session.query(Exam)
                .filter(Exam.user_id == user_id)
                .order_by(Exam.created_at.desc())
                .limit(50)
                .all()
            )
            result = []
            for r in rows:
                feedback = []
                try:
                    if hasattr(r, "feedback_json") and r.feedback_json:
                        feedback = json.loads(r.feedback_json)
                except Exception:
                    feedback = []
                result.append({
                    "id": r.id,
                    "created_at": r.created_at.isoformat() + "Z",
                    "score": r.score,
                    "topic_accuracy": json.loads(r.topic_stats_json or "{}"),
                    "feedback": feedback
                })
            return result
        finally:
            session.close()

    @app.get("/exam/{exam_id}")
    async def get_exam(exam_id: int, user_id: int = Depends(get_current_user_id)):
        session = ExamsSession()
        try:
            r = session.query(Exam).filter(Exam.id == exam_id, Exam.user_id == user_id).first()
            if not r:
                raise HTTPException(status_code=404, detail="Exam not found")
            feedback = []
            try:
                if hasattr(r, "feedback_json") and r.feedback_json:
                    feedback = json.loads(r.feedback_json)
            except Exception:
                feedback = []
            return {
                "id": r.id,
                "created_at": r.created_at.isoformat() + "Z",
                "questions": json.loads(r.questions_json or "[]"),
                "answers": json.loads(r.answers_json or "{}"),
                "score": r.score,
                "topic_accuracy": json.loads(r.topic_stats_json or "{}"),
                "feedback": feedback
            }
        finally:
            session.close()

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)


