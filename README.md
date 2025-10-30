# CodexEDU 🎓

AI-powered educational platform for personalized math exams and analytics.

## Tech
- Backend: FastAPI, SQLAlchemy, JWT
- Frontend: Streamlit
- DB: SQLite
- ML: numpy, scikit-learn (future extensions)

## Run
1) Install deps
```bash
pip install -r requirements.txt
```

2) Start backend API
```bash
python -m backend.main
# or
uvicorn backend.main:app --reload --port 8000
```

3) Start frontend
```bash
streamlit run frontend/app.py
```

Optional: In `.streamlit/secrets.toml` set:
```toml
api_base = "http://localhost:8000"
```

## API
- POST /auth/register -> {name, email, password}
- POST /auth/login -> {email, password}
- POST /exam/generate (Bearer) -> generate 10Q exam
- POST /exam/submit (Bearer) -> submit answers and get report
- GET /exam/me (Bearer) -> list my exams
- GET /exam/{id} (Bearer) -> exam detail

## Data
- data/users.db, data/exams.db
- data/ai_dataset.csv appends per-topic accuracy per exam

## Notes
- Question generation uses lightweight templates for reliability offline. Swap with OpenAI/HuggingFace easily in `backend/ai_engine/question_generator.py`.

