import logging
import json
import asyncio
from typing import AsyncGenerator, Dict, Any
from app.models.project import JenisIkan, Resiko
from app.service.generative.prompt_ringkasan_awal.gemini_client import GeminiClient
from app.service.generative.prompt_ringkasan_awal.context_helper import ContextHelper
from app.service.generative.prompt_ringkasan_awal.prompt_builder import PromptBuilder
from app.service.generative.prompt_ringkasan_awal.response_parser import ResponseParser

logger = logging.getLogger(__name__)

class ProjectAnalyzerStream:
    """Service untuk analisis project dengan streaming response"""
    
    def __init__(self):
        self.client = GeminiClient()
        self.context_helper = ContextHelper()
        self.prompt_builder = PromptBuilder()
        self.response_parser = ResponseParser()
    
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
        """Menganalisis project dengan streaming response
        
        Mengembalikan generator yang menghasilkan chunk-chunk response dari AI.
        Format: SSE (Server-Sent Events) dengan data JSON.
        """
        
        try:
            # 1. Setup dan kirim status awal
            skala, _ = self.context_helper.get_scale_info(modal)
            lokasi_multiplier = self.context_helper.get_location_context(kabupaten_id)
            ikan_data = self.context_helper.get_fish_context(jenis_ikan)
            
            prompt = self.prompt_builder.build_analysis_prompt(
                project_name, jenis_ikan, modal, 
                kabupaten_id, resiko, skala, lokasi_multiplier, ikan_data,
                lang=lang, lat=lat
            )
            
            logger.info(f"🔍 Mengirim streaming request ke Gemini API untuk analisis project: {project_name}")
            
            # 2. Kirim status "analyzing"
            yield f"data: {json.dumps({'status': 'analyzing', 'message': 'Sedang menganalisis project...'})}\n\n"
            
            # 3. Stream response dari Gemini
            full_response = ""
            try:
                response_stream = self.client.generate_content_stream(prompt)
                
                # Stream setiap chunk
                for chunk in response_stream:
                    if hasattr(chunk, 'text') and chunk.text:
                        full_response += chunk.text
                        # Kirim chunk ke client (untuk live preview)
                        yield f"data: {json.dumps({'status': 'streaming', 'chunk': chunk.text})}\n\n"
                    elif hasattr(chunk, 'parts') and chunk.parts:
                        for part in chunk.parts:
                            if hasattr(part, 'text') and part.text:
                                full_response += part.text
                                yield f"data: {json.dumps({'status': 'streaming', 'chunk': part.text})}\n\n"
                
                # 4. Parse response lengkap
                yield f"data: {json.dumps({'status': 'parsing', 'message': 'Memproses hasil analisis...'})}\n\n"
                
                cleaned_text = self.response_parser.clean_response_text(full_response)
                analysis_data = self.response_parser.parse_json_response(cleaned_text)
                
                # 5. Validasi dan normalisasi
                normalized_data = self.response_parser.validate_and_normalize_analysis(analysis_data)
                model_used = self.client.model_name
                
                # 6. Kirim hasil final
                final_result = {
                    "status": "completed",
                    "data": {
                        "skor_kelayakan": normalized_data["skor_kelayakan"],
                        "potensi_pasar": normalized_data["potensi_pasar"],
                        "estimasi_balik_modal": normalized_data["estimasi_balik_modal"],
                        "kesimpulan_ringkasan": normalized_data["kesimpulan_ringkasan"],
                        "ai_model_used": model_used,
                        "ai_analysis_success": True
                    }
                }
                
                logger.info(f"✅ Streaming analisis AI berhasil: Skor {normalized_data['skor_kelayakan']}/100")
                
                yield f"data: {json.dumps(final_result)}\n\n"
                
            except Exception as api_err:
                logger.error(f"❌ Error saat streaming dari Gemini API: {str(api_err)}")
                error_result = {
                    "status": "error",
                    "message": f"Error dari Gemini API: {str(api_err)}"
                }
                yield f"data: {json.dumps(error_result)}\n\n"
                
        except Exception as e:
            logger.error(f"❌ Error dalam streaming analisis: {str(e)}")
            error_result = {
                "status": "error",
                "message": f"Error dalam analisis: {str(e)}"
            }
            yield f"data: {json.dumps(error_result)}\n\n"

