import sys
from pathlib import Path
from fastapi import FastAPI, Depends, Request, HTTPException
from typing import Annotated
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Add current directory (app/) to sys.path so modules like models, database, routes can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))

import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from routes import client, admin

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically ensure tables exist on startup
    try:
        models.Base.metadata.create_all(bind=engine)
        print("[OK] Database tables verified / created.")
    except Exception as e:
        print(f"[WARNING] Database connection on startup: {e}")
    yield

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan
)

# Include Routers
app.include_router(client.router)
app.include_router(admin.router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# Mount static files for images and JS
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configure Jinja2 to look in the templates folder
templates = Jinja2Templates(directory="app/templates")

from fastapi.responses import RedirectResponse

@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc: HTTPException):
    if request.url.path.startswith("/admin") and request.url.path != "/admin/login":
        response = RedirectResponse("/admin/login", status_code=302)
        response.delete_cookie(key="access_token", path="/")
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return response

    return templates.TemplateResponse(
        request=request,
        name="401.html",
        status_code=401
    )
