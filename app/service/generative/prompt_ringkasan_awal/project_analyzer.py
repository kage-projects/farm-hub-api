import logging
from typing import Dict, Any
from app.models.project import JenisIkan, Resiko
from app.service.generative.prompt_ringkasan_awal.gemini_client import GeminiClient
from app.service.generative.prompt_ringkasan_awal.context_helper import ContextHelper
from app.service.generative.prompt_ringkasan_awal.prompt_builder import PromptBuilder
from app.service.generative.prompt_ringkasan_awal.response_parser import ResponseParser

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
        
        Semua hasil (skor_kelayakan, potensi_pasar, estimasi_balik_modal, kesimpulan_ringkasan)
        berasal 100% dari AI response, tidak ada perhitungan manual.
        """
        
        skala, _ = self.context_helper.get_scale_info(modal)
        lokasi_multiplier = self.context_helper.get_location_context(kabupaten_id)
        ikan_data = self.context_helper.get_fish_context(jenis_ikan)
        
        prompt = self.prompt_builder.build_analysis_prompt(
            project_name, jenis_ikan, modal, 
            kabupaten_id, resiko, skala, lokasi_multiplier, ikan_data,
            lang=lang, lat=lat
        )
        
        logger.info(f"🔍 Mengirim request ke Gemini API untuk analisis project: {project_name}")
        
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
                   f"ROI: {normalized_data['estimasi_balik_modal']} bulan, "
                   f"Model: {model_used}")
        
        # PENTING: Semua nilai di bawah ini 100% berasal dari AI response
        # TIDAK ADA perhitungan manual atau generate manual
        return {
            "skor_kelayakan": normalized_data["skor_kelayakan"],  # 100% dari AI
            "potensi_pasar": normalized_data["potensi_pasar"],  # 100% dari AI
            "estimasi_balik_modal": normalized_data["estimasi_balik_modal"],  # 100% dari AI
            "kesimpulan_ringkasan": normalized_data["kesimpulan_ringkasan"],  # 100% dari AI
            "ai_model_used": model_used,
            "ai_analysis_success": True  # Selalu True karena semua dari AI
        }
    
    def analyze_project_stream(
        self,
        project_name: str,
        jenis_ikan: JenisIkan,
        modal: int,
        kabupaten_id: str,
        resiko: Resiko,
        lang: float = None,
        lat: float = None
    ):
        """Menganalisis project dengan streaming response untuk mempercepat feedback
        
        Generator yang yield chunks dari response AI secara real-time
        """
        skala, _ = self.context_helper.get_scale_info(modal)
        lokasi_multiplier = self.context_helper.get_location_context(kabupaten_id)
        ikan_data = self.context_helper.get_fish_context(jenis_ikan)
        
        prompt = self.prompt_builder.build_analysis_prompt(
            project_name, jenis_ikan, modal, 
            kabupaten_id, resiko, skala, lokasi_multiplier, ikan_data,
            lang=lang, lat=lat
        )
        
        logger.info(f"🔍 Mengirim streaming request ke Gemini API untuk analisis project: {project_name}")
        
        try:
            # Kirim status awal
            yield {"type": "status", "message": "Mengirim request ke AI...", "progress": 10}
            
            # Generate dengan streaming
            stream = self.client.generate_content_stream(prompt)
            
            yield {"type": "status", "message": "Menerima response dari AI...", "progress": 30}
            
            # Kumpulkan semua chunks
            full_text = ""
            chunk_count = 0
            for chunk in stream:
                chunk_text = ""
                # Handle berbagai format chunk dari Gemini
                if hasattr(chunk, 'text'):
                    chunk_text = chunk.text
                elif hasattr(chunk, 'parts') and len(chunk.parts) > 0:
                    if hasattr(chunk.parts[0], 'text'):
                        chunk_text = chunk.parts[0].text
                elif isinstance(chunk, str):
                    chunk_text = chunk
                else:
                    # Skip chunk yang tidak bisa di-parse
                    continue
                
                if chunk_text:
                    full_text += chunk_text
                    chunk_count += 1
                    # Yield setiap chunk untuk real-time update (throttle untuk performa)
                    if chunk_count % 3 == 0:  # Yield setiap 3 chunks untuk mengurangi overhead
                        yield {"type": "chunk", "text": chunk_text, "progress": 50, "chunk_count": chunk_count}
            
            yield {"type": "status", "message": "Memproses response...", "progress": 70}
            
            # Parse dan validasi response
            cleaned_text = self.response_parser.clean_response_text(full_text)
            analysis_data = self.response_parser.parse_json_response(cleaned_text)
            normalized_data = self.response_parser.validate_and_normalize_analysis(analysis_data)
            
            model_used = self.client.model_name
            
            yield {"type": "status", "message": "Menyelesaikan analisis...", "progress": 90}
            
            # Yield hasil akhir
            result = {
                "type": "result",
                "data": {
                    "skor_kelayakan": normalized_data["skor_kelayakan"],
                    "potensi_pasar": normalized_data["potensi_pasar"],
                    "estimasi_balik_modal": normalized_data["estimasi_balik_modal"],
                    "kesimpulan_ringkasan": normalized_data["kesimpulan_ringkasan"],
                    "ai_model_used": model_used,
                    "ai_analysis_success": True
                },
                "progress": 100
            }
            yield result
            
            logger.info(f"✅ Streaming analisis AI berhasil: Skor {normalized_data['skor_kelayakan']}/100")
            
        except Exception as api_err:
            logger.error(f"❌ Error saat streaming dari Gemini API: {str(api_err)}")
            yield {
                "type": "error",
                "message": f"Error dari Gemini API: {str(api_err)}",
                "progress": 0
            }
            raise


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

