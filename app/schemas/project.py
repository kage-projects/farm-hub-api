from pydantic import BaseModel, Field
from app.models.project import JenisIkan, Resiko
from app.models.ringkasan_awal import PotensiPasar

class ProjectCreate(BaseModel):
    """Schema untuk create project"""
    project_name: str = Field(..., min_length=3, max_length=200)
    jenis_ikan: JenisIkan
    jumlah_team: int = Field(..., ge=1, description="1 = solo, >1 = team")
    modal: int = Field(..., gt=0, description="Modal dalam Rupiah")
    kabupaten_id: str = Field(..., description="ID/Nama kabupaten di Sumatera Barat")
    resiko: Resiko
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "Budidaya Lele di Padang",
                "jenis_ikan": "LELE",
                "jumlah_team": 1,
                "modal": 50000000,
                "kabupaten_id": "Padang",
                "resiko": "MODERAT"
            }
        }

class AIAnalysisInfo(BaseModel):
    """Schema untuk informasi analisis AI"""
    status: str = Field(..., description="Status analisis AI: 'success' atau 'failed'")
    model_used: str = Field(..., description="Model AI yang digunakan (contoh: gemini-1.5-flash)")
    source: str = Field(default="gemini", description="Sumber analisis")
    message: str = Field(..., description="Pesan status analisis")

class RingkasanAwalData(BaseModel):
    """Schema untuk data ringkasan awal"""
    skor_kelayakan: int
    potensi_pasar: str  # Menggunakan str untuk response, bisa berupa enum value
    estimasi_modal: int
    estimasi_balik_modal: int
    kesimpulan_ringkasan: str
    ai_analysis: AIAnalysisInfo = Field(..., description="Informasi analisis AI")

class ProjectData(BaseModel):
    """Schema untuk response project data"""
    id: str
    project_name: str
    jenis_ikan: str
    jumlah_team: int
    modal: int
    kabupaten_id: str
    resiko: str
    user_id: str

class ProjectResponse(BaseModel):
    """Schema untuk response create project"""
    success: bool
    message: str
    data: ProjectData
    ringkasan_awal: RingkasanAwalData

