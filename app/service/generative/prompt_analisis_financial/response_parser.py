import json
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ResponseParser:
    """Kelas untuk parsing dan validasi response dari Gemini API untuk analisis financial"""
    
    @staticmethod
    def extract_response_text(response) -> str:
        """Extract text dari response Gemini dengan berbagai format"""
        if not response:
            raise ValueError("Response dari Gemini API kosong atau None")
        
        if hasattr(response, 'text'):
            response_text = response.text
        elif hasattr(response, 'parts') and len(response.parts) > 0:
            response_text = response.parts[0].text if hasattr(response.parts[0], 'text') else str(response.parts[0])
        elif isinstance(response, str):
            response_text = response
        else:
            response_text = str(response)
        
        if not response_text:
            raise ValueError("Response text dari Gemini API kosong setelah extraction")
        
        return response_text.strip()
    
    @staticmethod
    def clean_response_text(response_text: str) -> str:
        """Membersihkan response text dari markdown dan whitespace"""
        response_text = response_text.strip()
        
        logger.debug(f"Raw response dari Gemini (first 500 chars): {response_text[:500]}")
        
        if not response_text:
            raise ValueError("Response text dari Gemini API kosong")
        
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        if "{" in response_text and "}" in response_text:
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            response_text = response_text[start_idx:end_idx]
        
        if not response_text or len(response_text) < 10:
            logger.error(f"Response text terlalu pendek atau kosong setelah cleaning: {response_text}")
            raise ValueError("Response dari Gemini API tidak valid atau kosong")
        
        return response_text.strip()
    
    @staticmethod
    def parse_json_response(response_text: str) -> Dict[str, Any]:
        """Parse JSON dari response text dengan error handling"""
        try:
            analysis_data = json.loads(response_text)
            return analysis_data
        except json.JSONDecodeError as json_err:
            logger.error(f"❌ Error parsing JSON dari Gemini:")
            logger.error(f"Response text: {response_text[:1000]}")
            logger.error(f"JSON Error: {str(json_err)}")
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    analysis_data = json.loads(json_match.group(0))
                    logger.info("✅ Berhasil extract JSON menggunakan regex fallback")
                    return analysis_data
                except:
                    raise ValueError(f"Gagal parsing JSON dari Gemini API. Response tidak valid: {response_text[:200]}")
            else:
                raise ValueError(f"Tidak ditemukan JSON valid dalam response Gemini API: {response_text[:200]}")
    
    @staticmethod
    def validate_and_normalize_analisis_financial(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validasi dan normalisasi data analisis financial dari AI"""
        
        required_sections = ["rincianModalAwal", "biayaOperasional", "analisisROI", "analisisBEP", "proyeksiPendapatan"]
        
        for section in required_sections:
            if section not in analysis_data:
                raise ValueError(f"Section {section} tidak ditemukan dalam response AI")
            
            if not isinstance(analysis_data[section], dict):
                raise ValueError(f"Section {section} harus berupa object/dictionary")
        
        # Validasi rincianModalAwal
        modal_fields = ["kolamTerpal", "pompaAir", "selangFilter", "pembelianBenih", "totalModalAwal"]
        for field in modal_fields:
            if field not in analysis_data["rincianModalAwal"]:
                raise ValueError(f"Field rincianModalAwal.{field} tidak ditemukan")
        
        # Validasi biayaOperasional
        operasional_fields = ["pakanBulanan", "listrik", "vitaminObat", "lainnya", "totalOperasionalBulanan"]
        for field in operasional_fields:
            if field not in analysis_data["biayaOperasional"]:
                raise ValueError(f"Field biayaOperasional.{field} tidak ditemukan")
        
        # Validasi analisisROI
        roi_fields = ["investasiAwal", "proyeksiKeuntunganPerSiklus", "roi", "lamaSiklus"]
        for field in roi_fields:
            if field not in analysis_data["analisisROI"]:
                raise ValueError(f"Field analisisROI.{field} tidak ditemukan")
        
        # Validasi analisisBEP (note: user typo "analisBEP" but we use correct "analisisBEP")
        bep_fields = ["modalAwal", "marginPerSiklus", "breakEvenPoint"]
        for field in bep_fields:
            if field not in analysis_data["analisisBEP"]:
                raise ValueError(f"Field analisisBEP.{field} tidak ditemukan")
        
        # Validasi proyeksiPendapatan
        pendapatan_fields = ["panenPerSiklusKg", "hargaPerKg", "pendapatanPerPanen"]
        for field in pendapatan_fields:
            if field not in analysis_data["proyeksiPendapatan"]:
                raise ValueError(f"Field proyeksiPendapatan.{field} tidak ditemukan")
        
        return analysis_data

