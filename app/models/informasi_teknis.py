import uuid
from sqlmodel import SQLModel, Field
from typing import Optional, Dict, Any
from sqlalchemy import JSON

class InformasiTeknis(SQLModel, table=True):
    """Model untuk informasi teknis project - One to One dengan Project"""
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    project_id: str = Field(
        foreign_key="projects.id",
        unique=True, 
        index=True
    )
    spesifikasi_kolam: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=JSON
    )
    kualitas_air: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=JSON
    )
    spesifikasi_benih: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=JSON
    )
    spesifikasi_pakan: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=JSON
    )
    manajemen_kesehatan: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=JSON
    )
    teknologi_pendukung: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=JSON
    )

    class Config:
        table_name = "informasi_teknis"

