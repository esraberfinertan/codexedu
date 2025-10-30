from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

# Ensure data directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

USERS_DB_URL = f"sqlite:///{os.path.join(DATA_DIR, 'users.db')}"
EXAMS_DB_URL = f"sqlite:///{os.path.join(DATA_DIR, 'exams.db')}"

UsersEngine = create_engine(USERS_DB_URL, connect_args={"check_same_thread": False})
ExamsEngine = create_engine(EXAMS_DB_URL, connect_args={"check_same_thread": False})

UsersSession = sessionmaker(bind=UsersEngine, autoflush=False, autocommit=False)
ExamsSession = sessionmaker(bind=ExamsEngine, autoflush=False, autocommit=False)

BaseUsers = declarative_base()
BaseExams = declarative_base()


class User(BaseUsers):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="student")
    created_at = Column(DateTime, default=datetime.utcnow)


class Exam(BaseExams):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    questions_json = Column(Text)  # List[Question]
    answers_json = Column(Text)  # Dict[question_id, selected_option]
    score = Column(Float, default=0.0)  # percentage 0-100
    topic_stats_json = Column(Text)  # Dict[topic, accuracy]
    feedback_json = Column(Text, nullable=True)  # per-question feedback list


def init_databases() -> None:
    BaseUsers.metadata.create_all(UsersEngine)
    BaseExams.metadata.create_all(ExamsEngine)
    # Safe migration for feedback_json
    import sqlite3
    try:
        conn = sqlite3.connect(EXAMS_DB_URL.replace('sqlite:///', ''))
        with conn:
            conn.execute("ALTER TABLE exams ADD COLUMN feedback_json TEXT DEFAULT '[]';")
    except Exception:
        pass


