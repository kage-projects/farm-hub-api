import logging
from typing import Dict, Any
from app.service.generative.prompt_analisis_financial.gemini_client import GeminiClient
from app.service.generative.prompt_analisis_financial.prompt_builder import PromptBuilder
from app.service.generative.prompt_analisis_financial.response_parser import ResponseParser

logger = logging.getLogger(__name__)

class AnalisisFinancialAnalyzer:
    """Service untuk generate analisis financial menggunakan Gemini AI"""
    
    def __init__(self):
        self.client = GeminiClient()
        self.prompt_builder = PromptBuilder()
        self.response_parser = ResponseParser()
    
    def generate_analisis_financial(
        self,
        project_name: str,
        jenis_ikan: str,
        modal: int,
        kabupaten_id: str,
        resiko: str,
        skor_kelayakan: int,
        potensi_pasar: str,
        estimasi_balik_modal: int,
        kesimpulan_ringkasan: str,
        informasi_teknis: dict,
        lang: float = None,
        lat: float = None
    ) -> Dict[str, Any]:
        """Generate analisis financial menggunakan AI"""
        
        prompt = self.prompt_builder.build_analisis_financial_prompt(
            project_name=project_name,
            jenis_ikan=jenis_ikan,
            modal=modal,
            kabupaten_id=kabupaten_id,
            resiko=resiko,
            skor_kelayakan=skor_kelayakan,
            potensi_pasar=potensi_pasar,
            estimasi_balik_modal=estimasi_balik_modal,
            kesimpulan_ringkasan=kesimpulan_ringkasan,
            informasi_teknis=informasi_teknis,
            lang=lang,
            lat=lat
        )
        
        logger.info(f"🔍 Mengirim request ke Gemini API untuk generate analisis financial: {project_name}")
        
        try:
            response = self.client.generate_content(prompt)
        except Exception as api_err:
            logger.error(f"❌ Error saat memanggil Gemini API: {str(api_err)}")
            raise Exception(f"Error dari Gemini API: {str(api_err)}")
        
        response_text = self.response_parser.extract_response_text(response)
        cleaned_text = self.response_parser.clean_response_text(response_text)
        analysis_data = self.response_parser.parse_json_response(cleaned_text)
        normalized_data = self.response_parser.validate_and_normalize_analisis_financial(analysis_data)
        
        logger.info(f"✅ Analisis financial berhasil di-generate untuk project: {project_name}")
        
        return normalized_data

