from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.routes.chat import router as chat_router
from backend.app.api.routes.auth import router as auth_router
from backend.app.db.session import create_tables
from backend.app.config import settings
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="AI-powered meeting minute chatbot for staff",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": f"{settings.app_name} is running",
        "version": "1.0.0",
        "status": "ok",
    }


@app.on_event("startup")
async def startup_event():
    create_tables()
    logger.info(f"{settings.app_name} started successfully")
    logger.info(f"Environment: {settings.app_env}")