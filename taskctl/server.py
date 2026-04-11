from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from .database import init_db, db_tasks_in_range
from .auth_store import (
    create_access_token,
    create_refresh_token,
    register_user,
    verify_password,
    verify_token,
)

app = FastAPI(title="taskctl API")


@app.on_event("startup")
def on_startup():
    init_db()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_bearer = HTTPBearer()


# ── Auth helpers ──────────────────────────────────────────────────────────────

def _current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> str:
    username = verify_token(credentials.credentials, "access")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return username


# ── Auth endpoints ────────────────────────────────────────────────────────────

class RegisterBody(BaseModel):
    first_name: str = ""
    last_name: str = ""
    username: str
    email: str = ""
    password: str


class TokenBody(BaseModel):
    username: str
    password: str


class RefreshBody(BaseModel):
    refresh: str


@app.post("/api/auth/register/")
def register(body: RegisterBody):
    try:
        register_user(
            username=body.username,
            password=body.password,
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {}


@app.post("/api/auth/token/")
def login(body: TokenBody):
    if not verify_password(body.username, body.password):
        raise HTTPException(status_code=400, detail="Invalid username or password.")
    return {
        "access": create_access_token(body.username),
        "refresh": create_refresh_token(body.username),
    }


@app.post("/api/auth/token/refresh/")
def refresh_token(body: RefreshBody):
    username = verify_token(body.refresh, "refresh")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")
    return {"access": create_access_token(username)}


# ── Tasks endpoint ────────────────────────────────────────────────────────────

@app.get("/api/tasks")
def get_tasks(
    days: int = Query(default=7, ge=1, le=365),
    current_user: str = Depends(_current_user),
) -> list[dict]:
    return db_tasks_in_range(days)
