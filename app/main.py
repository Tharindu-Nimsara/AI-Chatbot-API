from fastapi import FastAPI
from app.core.config import settings
from app.core.database import initialize_database
from app.api.chat import router as chat_router
from app.api.history import router as history_router
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="AI Chatbot API with memory and LLM integration"
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    initialize_database()

# Register routers
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