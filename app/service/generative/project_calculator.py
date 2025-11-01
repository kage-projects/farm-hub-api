import random
from typing import Dict, Tuple, Any
from app.models.project import JenisIkan, Resiko

class ProjectCalculator:
    
    @staticmethod
    def calculate_scale(modal: int) -> Tuple[str, float]:
        """Menghitung skala project berdasarkan modal"""
        if modal < 30000000:
            return "Kecil", 0.9
        elif modal < 75000000:
            return "Menengah", 1.0
        elif modal < 150000000:
            return "Besar", 1.15
        else:
            return "Sangat Besar", 1.25
    
    @staticmethod
    def get_risk_multiplier(resiko: Resiko) -> float:
        """Mendapatkan faktor resiko"""
        resiko_multiplier = {
            "KONSERVATIF": 0.95,
            "MODERAT": 1.0,
            "AGRESIF": 1.1
        }
        return resiko_multiplier.get(resiko.value, 1.0)
    
    @staticmethod
    def get_location_multiplier(kabupaten_id: str) -> float:
        """Mendapatkan faktor lokasi"""
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
    def get_fish_data(jenis_ikan: JenisIkan) -> Dict[str, Any]:
        """Mendapatkan data faktor jenis ikan"""
        ikan_faktor = {
            "LELE": {"potensi": 1.15, "modal_adj": 1.0, "roi_months": 10},
            "NILA": {"potensi": 1.05, "modal_adj": 1.1, "roi_months": 14},
            "GURAME": {"potensi": 0.95, "modal_adj": 1.2, "roi_months": 16}
        }
        return ikan_faktor.get(jenis_ikan.value, {"potensi": 1.0, "modal_adj": 1.0, "roi_months": 12})
    
    @staticmethod
    def calculate_estimated_roi(skala: str, base_roi: int) -> int:
        """Menghitung estimasi ROI berdasarkan jenis ikan dan skala"""
        if skala == "Kecil":
            roi_adjust = random.uniform(1.0, 1.3)
        elif skala == "Besar":
            roi_adjust = random.uniform(0.8, 0.95)
        else:
            roi_adjust = random.uniform(0.9, 1.1)
        return int(base_roi * roi_adjust)
    
    @staticmethod
    def calculate_feasibility_score(
        modal: int,
        lokasi_multiplier: float,
        ikan_potensi: float,
        resiko: Resiko
    ) -> int:
        """Menghitung skor kelayakan"""
        base_score = 60
        score_modal = min(20, (modal / 100000000) * 20) if modal > 0 else 10
        score_lokasi = lokasi_multiplier * 10
        score_ikan = ikan_potensi * 10
        score_resiko = {"KONSERVATIF": 10, "MODERAT": 8, "AGRESIF": 5}.get(resiko.value, 5)
        
        calculated_score = base_score + score_modal + score_lokasi + score_ikan + score_resiko
        return min(95, max(40, int(calculated_score)))
    
    @staticmethod
    def determine_market_potential(lokasi_multiplier: float, ikan_potensi: float) -> str:
        """Menentukan potensi pasar"""
        if lokasi_multiplier >= 1.1 and ikan_potensi >= 1.1:
            return "TINGGI"
        elif lokasi_multiplier >= 1.0 and ikan_potensi >= 1.0:
            return "SEDANG"
        else:
            return "RENDAH"

