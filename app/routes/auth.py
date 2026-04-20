import sqlite3

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.auth import create_token, decode_token, hash_password, verify_password
from app.database import get_db

router = APIRouter()


class AuthRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    country: str = ""
    phone: str = ""


def _current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required.")
    user_id = decode_token(authorization.split(" ", 1)[1])
    if not user_id:
        raise HTTPException(401, "Invalid or expired session. Please log in again.")
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()
    if not user:
        raise HTTPException(401, "Account not found.")
    return dict(user)


@router.post("/register")
def register(req: RegisterRequest):
    email = req.email.lower().strip()
    if not email or "@" not in email:
        raise HTTPException(400, "Please enter a valid email address.")
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters.")
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (email, password_hash, tries_remaining, country, phone) VALUES (?, ?, 3, ?, ?)",
            (email, hash_password(req.password), req.country.strip(), req.phone.strip()),
        )
        db.commit()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return {
            "token":           create_token(user["id"]),
            "email":           user["email"],
            "tries_remaining": user["tries_remaining"],
        }
    except sqlite3.IntegrityError:
        raise HTTPException(400, "An account with this email already exists. Please sign in instead.")
    except Exception as e:
        raise HTTPException(500, f"Registration failed. Please try again.")
    finally:
        db.close()


@router.post("/login")
def login(req: AuthRequest):
    email = req.email.lower().strip()
    db = get_db()
    try:
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not user or not verify_password(req.password, user["password_hash"]):
            raise HTTPException(401, "Incorrect email or password.")
        return {
            "token":           create_token(user["id"]),
            "email":           user["email"],
            "tries_remaining": user["tries_remaining"],
        }
    finally:
        db.close()


@router.get("/me")
def me(authorization: str = Header(None)):
    user = _current_user(authorization)
    return {"email": user["email"], "tries_remaining": user["tries_remaining"]}
