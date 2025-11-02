from pydantic import BaseModel, Field
from typing import Optional
from app.models.project import JenisIkan, Resiko
from app.models.ringkasan_awal import PotensiPasar

class ProjectCreate(BaseModel):
    """Schema untuk create project"""
    project_name: Optional[str] = Field(None, min_length=3, max_length=200, description="Nama project (opsional, akan auto-generate jika tidak diisi)")
    jenis_ikan: JenisIkan
    modal: int = Field(..., gt=0, description="Modal dalam Rupiah")
    kabupaten_id: str = Field(..., description="ID/Nama kabupaten di Sumatera Barat")
    resiko: Resiko
    lang: Optional[float] = Field(None, description="Longitude")
    lat: Optional[float] = Field(None, description="Latitude")
    
    class Config:
        json_schema_extra = {
            "example": {
                "jenis_ikan": "LELE",
                "modal": 50000000,
                "kabupaten_id": "Padang",
                "resiko": "MODERAT",
                "lang": 100.3543,
                "lat": -0.9492
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
    potensi_pasar: str  
    estimasi_balik_modal: int
    kesimpulan_ringkasan: str
    ai_analysis: AIAnalysisInfo = Field(..., description="Informasi analisis AI")

class ProjectData(BaseModel):
    """Schema untuk response project data"""
    id: str
    project_name: str
    jenis_ikan: str
    modal: int
    kabupaten_id: str
    resiko: str
    user_id: str
    lang: Optional[float] = None
    lat: Optional[float] = None

class ProjectUpdate(BaseModel):
    """Schema untuk update project (partial update - semua field optional)"""
    project_name: Optional[str] = Field(None, min_length=3, max_length=200)
    jenis_ikan: Optional[JenisIkan] = None
    modal: Optional[int] = Field(None, gt=0, description="Modal dalam Rupiah")
    kabupaten_id: Optional[str] = None
    resiko: Optional[Resiko] = None
    lang: Optional[float] = Field(None, description="Longitude")
    lat: Optional[float] = Field(None, description="Latitude")
    
    class Config:
        json_schema_extra = {
            "example": {
                "modal": 60000000,
                "lang": 100.3543,
                "lat": -0.9492
            }
        }

class ProjectUpdateResponse(BaseModel):
    """Schema untuk response update project"""
    success: bool
    message: str
    data: ProjectData
    ringkasan_awal: RingkasanAwalData

class RingkasanAwalDataSimple(BaseModel):
    """Schema untuk data ringkasan awal (tanpa ai_analysis) - untuk GET project"""
    ringkasanId: str
    skor_kelayakan: int
    potensi_pasar: str  
    estimasi_balik_modal: int
    kesimpulan_ringkasan: str

class ProjectResponse(BaseModel):
    """Schema untuk response create project"""
    success: bool
    message: str
    data: ProjectData
    ringkasan_awal: RingkasanAwalData

class ProjectDetailResponse(BaseModel):
    """Schema untuk response GET project detail"""
    success: bool
    message: str
    data: ProjectData
    ringkasan_awal: RingkasanAwalDataSimple

class ProjectListItem(BaseModel):
    """Schema untuk item dalam list project (simplified)"""
    id: str
    project_name: str
    kabupaten_id: str
    resiko: str

class ProjectListResponse(BaseModel):
    """Schema untuk response GET list projects"""
    success: bool
    message: str
    data: list[ProjectListItem]

from typing import Any, Dict, List, Optional

class InformasiTeknisResponse(BaseModel):
    """Schema untuk informasi teknis response"""
    spesifikasiKolam: Dict[str, Any]
    kualitasAir: Dict[str, Any]
    spesifikasiBenih: Dict[str, Any]
    spesifikasiPakan: Dict[str, Any]
    manajemenKesehatan: Dict[str, Any]
    teknologiPendukung: Dict[str, Any]

class AnalisisFinancialResponse(BaseModel):
    """Schema untuk analisis financial response"""
    rincianModalAwal: Dict[str, Any]
    biayaOperasional: Dict[str, Any]
    analisisROI: Dict[str, Any]
    analisisBEP: Dict[str, Any]
    proyeksiPendapatan: Dict[str, Any]

class RoadmapStep(BaseModel):
    """Schema untuk step dalam roadmap"""
    step: float
    title: str
    deskripsi: str

class RoadmapResponse(BaseModel):
    """Schema untuk roadmap response"""
    response: Dict[str, Any]
    request: Optional[str] = None
    step: float
    isRequest: bool
    roadmapId: Optional[str] = None

class AnalyzeResponse(BaseModel):
    """Schema untuk response endpoint analyze"""
    success: bool
    message: str
    data: Dict[str, Any]

class RoadmapStepRequest(BaseModel):
    """Schema untuk request update roadmap step"""
    request: str = Field(..., min_length=5, description="Input/masukkan dari user untuk sub-step")
    step: int = Field(default=1, ge=1, le=4, description="Nomor step utama yang akan ditambahkan sub-stepnya (1-4)")

class RoadmapStepUpdateResponse(BaseModel):
    """Schema untuk response update roadmap step"""
    success: bool
    message: str
    data: Dict[str, Any]

