from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.auth import create_token, decode_token, hash_password, verify_password
from app.database import IntegrityError, get_db

router = APIRouter()


class AuthRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    country: str = ""
    phone: str = ""
    gdpr_consent: bool = False


class UpdateAccountRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    current_password: str | None = None
    new_password: str | None = None


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
    return user


@router.post("/register")
def register(req: RegisterRequest):
    email = req.email.lower().strip()
    if not email or "@" not in email:
        raise HTTPException(400, "Please enter a valid email address.")
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters.")
    if not req.gdpr_consent:
        raise HTTPException(400, "You must accept the Privacy Policy to create an account.")
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (email, password_hash, tries_remaining, country, phone, gdpr_consent) VALUES (?, ?, 3, ?, ?, ?)",
            (email, hash_password(req.password), req.country.strip(), req.phone.strip(), req.gdpr_consent),
        )
        db.commit()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return {
            "token":           create_token(user["id"]),
            "email":           user["email"],
            "tries_remaining": user["tries_remaining"],
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "An account with this email already exists. Please sign in.")
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Registration failed: {type(e).__name__}: {e}")
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
    return {"email": user["email"], "name": user.get("name", ""), "tries_remaining": user["tries_remaining"]}


@router.patch("/account")
def update_account(req: UpdateAccountRequest, authorization: str = Header(None)):
    user = _current_user(authorization)
    db = get_db()
    try:
        if req.name is not None:
            name = req.name.strip()
            db.execute("UPDATE users SET name = ? WHERE id = ?", (name, user["id"]))
            db.commit()
            return {"name": name}

        if req.email is not None:
            if not req.current_password:
                raise HTTPException(400, "Current password is required to change email.")
            if not verify_password(req.current_password, user["password_hash"]):
                raise HTTPException(400, "Incorrect current password.")
            new_email = req.email.lower().strip()
            if "@" not in new_email:
                raise HTTPException(400, "Please enter a valid email address.")
            try:
                db.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user["id"]))
                db.commit()
            except IntegrityError:
                db.rollback()
                raise HTTPException(400, "This email is already in use by another account.")
            return {"email": new_email}

        if req.new_password is not None:
            if not req.current_password:
                raise HTTPException(400, "Current password is required.")
            if not verify_password(req.current_password, user["password_hash"]):
                raise HTTPException(400, "Incorrect current password.")
            if len(req.new_password) < 6:
                raise HTTPException(400, "New password must be at least 6 characters.")
            db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                       (hash_password(req.new_password), user["id"]))
            db.commit()
            return {"message": "Password updated successfully."}

        raise HTTPException(400, "No update fields provided.")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Update failed: {e}")
    finally:
        db.close()


@router.delete("/account")
def delete_account(authorization: str = Header(None)):
    user = _current_user(authorization)
    db = get_db()
    try:
        db.execute("DELETE FROM users WHERE id = ?", (user["id"],))
        db.commit()
        return {"message": "Account deleted successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Could not delete account: {e}")
    finally:
        db.close()
