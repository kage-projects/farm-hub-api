import uuid
from enum import Enum
from sqlmodel import SQLModel, Field, Column, String
from typing import Optional
from app.models.user import User  

class Resiko(str, Enum):
    """Enum untuk tingkat resiko investasi"""
    KONSERVATIF = "KONSERVATIF"
    MODERAT = "MODERAT"
    AGRESIF = "AGRESIF"

class JenisIkan(str, Enum):
    """Enum untuk jenis ikan budidaya"""
    NILA = "NILA"
    LELE = "LELE"
    GURAME = "GURAME"

class Project(SQLModel, table=True):
    """Model untuk project budidaya ikan"""
    __tablename__ = "projects"
    
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    project_name: str = Field(index=True)
    user_id: str = Field(
        foreign_key="users.id",
        index=True
    )
    kabupaten_id: str
    jenis_ikan: JenisIkan = Field(
        sa_column=Column(String)
    )
    jumlahTeam : int
    modal: int
    resiko: Resiko = Field(
        sa_column=Column(String)
    )

