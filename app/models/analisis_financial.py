import uuid
from sqlmodel import SQLModel, Field
from typing import Optional, Dict, Any
from sqlalchemy import JSON

class AnalisisFinancial(SQLModel, table=True):
    """Model untuk analisis financial project - One to One dengan Project"""
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    project_id: str = Field(
        foreign_key="projects.id",
        unique=True, 
        index=True
    )
    rincian_modal_awal: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=JSON
    )
    biaya_operasional: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=JSON
    )
    analisis_roi: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=JSON
    )
    analisis_bep: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=JSON
    )
    proyeksi_pendapatan: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=JSON
    )

    class Config:
        table_name = "analisis_financial"

