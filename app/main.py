from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title="E-Commerce API",
    description="A production-ready e-commerce backend API built with FastAPI, SQLAlchemy (Async), and Stripe.",
    version="1.0.0",
    contact={
        "name": "Admin",
        "email": "admin@example.com",
    },
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS middleware - must be added before routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8090",  # Docker frontend (Nginx)
        "http://localhost:5173",  # Vite dev server (default)
        "http://localhost:5174",  # Vite dev server (alternative port)
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",  # Vite dev server (127.0.0.1)
        "http://127.0.0.1:5174",  # Vite dev server (127.0.0.1 alternative)
    ],
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
