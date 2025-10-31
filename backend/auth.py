from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import os
import jwt
from passlib.hash import pbkdf2_sha256

from database import UsersSession, User


router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_change_me")
JWT_ALG = "HS256"
JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", "60"))


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def hash_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pbkdf2_sha256.verify(password, password_hash)


def create_access_token(sub: str) -> str:
    exp = datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES)
    payload = {"sub": sub, "exp": exp}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return token


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except Exception:
        return None


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest):
    session: Session = UsersSession()
    try:
        exists = session.query(User).filter(User.email == body.email).first()
        if exists:
            raise HTTPException(status_code=400, detail="Email already registered")
        user = User(
            name=body.name,
            email=body.email,
            password_hash=hash_password(body.password),
            role="student",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        token = create_access_token(str(user.id))
        return TokenResponse(access_token=token)
    finally:
        session.close()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    session: Session = UsersSession()
    try:
        user = session.query(User).filter(User.email == body.email).first()
        if not user or not verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token(str(user.id))
        return TokenResponse(access_token=token)
    finally:
        session.close()


