import uuid
from enum import Enum
from sqlmodel import SQLModel, Field, Column, String
from typing import Optional

class PotensiPasar(str, Enum):
    """Enum untuk potensi pasar"""
    TINGGI = "TINGGI"
    SEDANG = "SEDANG"
    RENDAH = "RENDAH"

class RingkasanAwal(SQLModel, table=True):
    """Model untuk ringkasan awal project - One to One dengan Project"""
    __tablename__ = "ringkasan_awal"
    
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    project_id: str = Field(
        foreign_key="projects.id",
        unique=True, 
        index=True
    )
    skor_kelayakan: int
    potensi_pasar: PotensiPasar = Field(
        sa_column=Column(String)
    )
    estimasi_modal: int
    estimasi_balik_modal: int
    kesimpulan_ringkasan: str

