import logging
from typing import Dict, Any
from app.models.project import JenisIkan, Resiko
from app.service.generative.gemini_client import GeminiClient
from app.service.generative.context_helper import ContextHelper
from app.service.generative.prompt_builder import PromptBuilder
from app.service.generative.response_parser import ResponseParser

logger = logging.getLogger(__name__)

class ProjectAnalyzer:
    """Service utama untuk analisis project menggunakan Gemini AI - FULL AI, tidak ada generate manual"""
    
    def __init__(self):
        self.client = GeminiClient()
        self.context_helper = ContextHelper()
        self.prompt_builder = PromptBuilder()
        self.response_parser = ResponseParser()
    
    def analyze_project(
        self,
        project_name: str,
        jenis_ikan: JenisIkan,
        modal: int,
        kabupaten_id: str,
        resiko: Resiko,
        lang: float = None,
        lat: float = None
    ) -> Dict[str, Any]:
        """Menganalisis project menggunakan AI - FULL AI RESPONSE, tidak ada generate manual
        
        Semua hasil (skor_kelayakan, potensi_pasar, estimasi_modal, estimasi_balik_modal, kesimpulan_ringkasan)
        berasal 100% dari AI response, tidak ada perhitungan manual.
        """
        
        # Ambil konteks HANYA untuk membantu AI memahami context (TIDAK untuk generate hasil)
        skala, _ = self.context_helper.get_scale_info(modal)
        lokasi_multiplier = self.context_helper.get_location_context(kabupaten_id)
        ikan_data = self.context_helper.get_fish_context(jenis_ikan)
        
        # Build prompt dengan konteks HANYA untuk membantu AI memahami context (TIDAK untuk generate hasil)
        prompt = self.prompt_builder.build_analysis_prompt(
            project_name, jenis_ikan, modal, 
            kabupaten_id, resiko, skala, lokasi_multiplier, ikan_data,
            lang=lang, lat=lat
        )
        
        logger.info(f"🔍 Mengirim request ke Gemini API untuk analisis project: {project_name}")
        
        # Generate response dari AI
        try:
            response = self.client.generate_content(prompt)
        except Exception as api_err:
            logger.error(f"❌ Error saat memanggil Gemini API: {str(api_err)}")
            raise Exception(f"Error dari Gemini API: {str(api_err)}")
        
        # Parse dan validasi response dari AI
        response_text = self.response_parser.extract_response_text(response)
        cleaned_text = self.response_parser.clean_response_text(response_text)
        analysis_data = self.response_parser.parse_json_response(cleaned_text)
        
        # Validasi bahwa semua data berasal dari AI (tanpa fallback manual)
        normalized_data = self.response_parser.validate_and_normalize_analysis(analysis_data)
        
        model_used = self.client.model_name
        
        logger.info(f"✅ Analisis AI berhasil: Skor {normalized_data['skor_kelayakan']}/100, "
                   f"Modal: {normalized_data['estimasi_modal']:,}, "
                   f"ROI: {normalized_data['estimasi_balik_modal']} bulan, "
                   f"Model: {model_used}")
        
        # PENTING: Semua nilai di bawah ini 100% berasal dari AI response
        # TIDAK ADA perhitungan manual atau generate manual
        return {
            "skor_kelayakan": normalized_data["skor_kelayakan"],  # 100% dari AI
            "potensi_pasar": normalized_data["potensi_pasar"],  # 100% dari AI
            "estimasi_modal": normalized_data["estimasi_modal"],  # 100% dari AI
            "estimasi_balik_modal": normalized_data["estimasi_balik_modal"],  # 100% dari AI
            "kesimpulan_ringkasan": normalized_data["kesimpulan_ringkasan"],  # 100% dari AI
            "ai_model_used": model_used,
            "ai_analysis_success": True  # Selalu True karena semua dari AI
        }


# Function untuk backward compatibility
def analyze_project_with_gemini(
    project_name: str,
    jenis_ikan: JenisIkan,
    modal: int,
    kabupaten_id: str,
    resiko: Resiko,
    lang: float = None,
    lat: float = None
) -> Dict[str, Any]:
    """Function wrapper untuk backward compatibility dengan kode lama"""
    analyzer = ProjectAnalyzer()
    return analyzer.analyze_project(
        project_name, jenis_ikan, modal, kabupaten_id, resiko, lang=lang, lat=lat
    )

