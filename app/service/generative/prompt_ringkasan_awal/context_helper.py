from typing import Dict, Tuple, Any
from app.models.project import JenisIkan

class ContextHelper:
    """Helper class untuk memberikan konteks ke AI prompt - TIDAK untuk generate hasil"""
    
    @staticmethod
    def get_scale_info(modal: int) -> Tuple[str, float]:
        """Mendapatkan informasi skala project untuk konteks prompt"""
        if modal < 30000000:
            return "Kecil", 0.9
        elif modal < 75000000:
            return "Menengah", 1.0
        elif modal < 150000000:
            return "Besar", 1.15
        else:
            return "Sangat Besar", 1.25
    
    @staticmethod
    def get_location_context(kabupaten_id: str) -> float:
        """Mendapatkan konteks lokasi untuk prompt - nilai hanya untuk referensi AI"""
        lokasi_faktor = {
            "Padang": 1.15,
            "Bukittinggi": 1.1,
            "Padang Panjang": 1.05,
            "Pariaman": 1.0,
            "Solok": 0.95,
            "Sawahlunto": 0.9,
            "Payakumbuh": 1.05
        }
        return lokasi_faktor.get(kabupaten_id.title(), 1.0)
    
    @staticmethod
    def get_fish_context(jenis_ikan: JenisIkan) -> Dict[str, Any]:
        """Mendapatkan konteks jenis ikan untuk prompt - data hanya untuk referensi AI"""
        ikan_faktor = {
            "LELE": {"potensi": 1.15, "modal_adj": 1.0, "roi_months": 10},
            "NILA": {"potensi": 1.05, "modal_adj": 1.1, "roi_months": 14},
            "GURAME": {"potensi": 0.95, "modal_adj": 1.2, "roi_months": 16}
        }
        return ikan_faktor.get(jenis_ikan.value, {"potensi": 1.0, "modal_adj": 1.0, "roi_months": 12})

