from fastapi import FastAPI
from app.config import get_settings
from app.database import init_db
from app.routes import api_router
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version
)

@app.on_event("startup")
def startup():
    logger.info("🚀 Starting application...")
    try:
        init_db()
        logger.info("✅ Startup completed!")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

app.include_router(api_router)

@app.get("/")
def root():
    return {"status": "ok", "message": "FarmHub API"}

def main():  
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

if __name__ == "__main__":  
    main()