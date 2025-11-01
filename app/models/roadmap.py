import uuid
from sqlmodel import SQLModel, Field, Column
from typing import Optional, Any
from sqlalchemy import JSON

class Roadmap(SQLModel, table=True):
    """Model untuk roadmap project"""
    __tablename__ = "roadmaps"
    
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    project_id: str = Field(
        foreign_key="projects.id",
        index=True
    )
    response: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    request: Optional[str] = None
    step: float
    is_request: bool
    roadmap_id: Optional[str] = Field(
        default=None,
        foreign_key="roadmaps.id",
        index=True
    )

