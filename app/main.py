from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app import models
from app.routers import auth, properties, dashboard, inquiries
from app.i18n import get_lang, get_t, SUPPORTED_LANGS, FLAGS
import os

# Create all tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Property Antalya", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Routers
app.include_router(auth.router)
app.include_router(properties.router)
app.include_router(dashboard.router)
app.include_router(inquiries.router)


@app.get("/lang/{code}")
def set_language(code: str, request: Request):
    referer = request.headers.get("referer", "/")
    response = RedirectResponse(url=referer, status_code=302)
    if code in SUPPORTED_LANGS:
        response.set_cookie("lang", code, max_age=365 * 24 * 3600, samesite="lax")
    return response
