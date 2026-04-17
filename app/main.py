from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import initialize_database
from app.api.chat import router as chat_router
from app.api.history import router as history_router
from app.middleware.security_middleware import SecurityHeadersMiddleware
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    initialize_database()
    yield
    # Shutdown (add cleanup here later if needed)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="AI Chatbot API with memory and LLM integration",
    lifespan=lifespan
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origins],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"]
)

app.include_router(chat_router)
app.include_router(history_router)


@app.get("/")
async def root():
    return {
        "message": "AI Chatbot API is running",
        "version": settings.app_version
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}