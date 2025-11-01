import uuid
from sqlmodel import SQLModel, Field
from typing import Optional

class Suplier(SQLModel, table=True):
    """Model untuk suplier/toko suplier"""
    __tablename__ = "suplier"
    
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    lang: str = Field(description="Longitude")
    lat: str = Field(description="Latitude")
    namaToko: str = Field(index=True, description="Nama toko suplier")
    rating: int = Field(description="Rating suplier (0-5)")
    alamat: str = Field(description="Alamat lengkap suplier")
    noHp: str = Field(description="Nomor HP suplier")
    projectId: str = Field(
        foreign_key="projects.id",
        index=True,
        description="ID project yang menggunakan suplier ini"
    )

