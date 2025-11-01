import uuid
from sqlmodel import SQLModel, Field, Column
from typing import Optional, Any
from sqlalchemy import JSON

class InformasiTeknis(SQLModel, table=True):
    """Model untuk informasi teknis project - One to One dengan Project"""
    __tablename__ = "informasi_teknis"
    
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    project_id: str = Field(
        foreign_key="projects.id",
        unique=True, 
        index=True
    )
    spesifikasi_kolam: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    kualitas_air: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    spesifikasi_benih: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    spesifikasi_pakan: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    manajemen_kesehatan: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    teknologi_pendukung: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON)
    )

