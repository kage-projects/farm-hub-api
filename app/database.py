from sqlmodel import SQLModel, create_engine, Session
from app.config import get_settings
from app.models import User
import logging

logger = logging.getLogger(__name__)

settings = get_settings()
engine = create_engine(settings.database_url, echo=True) 

def init_db():
    """Initialize database - Create all tables"""
    logger.info("Initializing database...")
    logger.info(f"Database URL: {settings.database_url}")
    logger.info(f"Models registered: {list(SQLModel.metadata.tables.keys())}")
    
    try:
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        raise

def get_session():
    with Session(engine) as session:
        yield session