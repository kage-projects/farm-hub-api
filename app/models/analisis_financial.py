import uuid
from sqlmodel import SQLModel, Field, Column
from typing import Optional, Any
from sqlalchemy import JSON

class AnalisisFinancial(SQLModel, table=True):
    """Model untuk analisis financial project - One to One dengan Project"""
    __tablename__ = "analisis_financial"
    
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    project_id: str = Field(
        foreign_key="projects.id",
        unique=True, 
        index=True
    )
    rincian_modal_awal: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    biaya_operasional: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    analisis_roi: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    analisis_bep: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    proyeksi_pendapatan: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON)
    )

