import uuid
from enum import Enum
from sqlmodel import SQLModel, Field, Column, String
from typing import Optional

class TipeProduk(str, Enum):
    """Enum untuk tipe produk"""
    BENIH = "BENIH"
    PAKAN = "PAKAN"
    ALAT = "ALAT"
    OBAT = "OBAT"
    LAINNYA = "LAINNYA"

class Produk(SQLModel, table=True):
    """Model untuk produk dari suplier"""
    __tablename__ = "produk"
    
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    namaProduk: str = Field(index=True, description="Nama produk")
    tipe: TipeProduk = Field(
        sa_column=Column(String),
        description="Tipe produk"
    )
    harga: int = Field(description="Harga produk dalam Rupiah")
    suplierId: str = Field(
        foreign_key="suplier.id",
        index=True,
        description="ID suplier yang menyediakan produk ini"
    )

