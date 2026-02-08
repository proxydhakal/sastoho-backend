from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.api import api_router

# Disable OpenAPI docs in production when DEBUG is False
_docs_url = None if (settings.is_production and not settings.DEBUG) else "/docs"
_redoc_url = None if (settings.is_production and not settings.DEBUG) else "/redoc"
_openapi_url = None if (settings.is_production and not settings.DEBUG) else f"{settings.API_V1_STR}/openapi.json"

app = FastAPI(
    title="E-Commerce API",
    description="A production-ready e-commerce backend API built with FastAPI, SQLAlchemy (Async), and Stripe.",
    version="1.0.0",
    contact={
        "name": "Admin",
        "email": "admin@example.com",
    },
    debug=settings.DEBUG,
    openapi_url=_openapi_url,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)

# CORS: use config (CORS_ORIGINS in .env; production should set exact frontend URL(s))
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount static files for uploaded images and logo
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.PROJECT_NAME}
