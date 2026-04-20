import pathlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routes import analyze, annotate, pdf
from app.routes import auth

app = FastAPI(title=settings.app_name, docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router,     prefix="/api")
app.include_router(analyze.router,  prefix="/api")
app.include_router(annotate.router, prefix="/api")
app.include_router(pdf.router,      prefix="/api")

@app.on_event("startup")
def startup():
    init_db()

_HTML       = pathlib.Path("templates/index.html").read_text(encoding="utf-8")
_LOGIN_HTML = pathlib.Path("templates/login.html").read_text(encoding="utf-8")
_APP_HTML   = pathlib.Path("templates/app_page.html").read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(_HTML.replace("{{ app_name }}", settings.app_name))


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(_LOGIN_HTML.replace("{{ app_name }}", settings.app_name))


@app.get("/app", response_class=HTMLResponse)
async def app_page():
    return HTMLResponse(_APP_HTML.replace("{{ app_name }}", settings.app_name))
