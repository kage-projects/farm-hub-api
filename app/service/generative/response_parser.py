import json
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ResponseParser:
    """Kelas untuk parsing dan validasi response dari Gemini API"""
    
    @staticmethod
    def extract_response_text(response) -> str:
        """Extract text dari response Gemini dengan berbagai format"""
        if not response:
            raise ValueError("Response dari Gemini API kosong atau None")
        
        # Handle berbagai tipe response dari Gemini
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
        
        # Log raw response untuk debugging
        logger.debug(f"Raw response dari Gemini (first 500 chars): {response_text[:500]}")
        
        if not response_text:
            raise ValueError("Response text dari Gemini API kosong")
        
        # Clean response - remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Remove ```json
        elif response_text.startswith("```"):
            response_text = response_text[3:]  # Remove ```
        
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Remove closing ```
        
        response_text = response_text.strip()
        
        # Cari JSON object dalam response (jika ada text tambahan)
        if "{" in response_text and "}" in response_text:
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            response_text = response_text[start_idx:end_idx]
        
        # Validasi response tidak kosong
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
            
            # Coba extract JSON menggunakan regex sebagai fallback
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
    def validate_and_normalize_analysis(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validasi dan normalisasi data analisis dari AI - FULL AI RESPONSE
        
        PENTING: Semua nilai yang dikembalikan HARUS berasal dari AI response.
        TIDAK ADA fallback ke perhitungan manual.
        Jika AI tidak memberikan field yang diperlukan, akan raise ValueError.
        """
        
        # Validasi bahwa semua field yang diperlukan ada dari AI
        required_fields = ["skor_kelayakan", "potensi_pasar", "estimasi_balik_modal", "kesimpulan_ringkasan"]
        missing_fields = [field for field in required_fields if field not in analysis_data or analysis_data[field] is None]
        
        if missing_fields:
            raise ValueError(
                f"AI tidak memberikan semua field yang diperlukan. Field yang hilang: {', '.join(missing_fields)}. "
                f"Response: {str(analysis_data)}"
            )
        
        # Validasi tipe dan range untuk skor kelayakan
        skor_kelayakan = analysis_data["skor_kelayakan"]
        if not isinstance(skor_kelayakan, (int, float)):
            try:
                skor_kelayakan = int(float(str(skor_kelayakan).strip()))
            except (ValueError, TypeError):
                raise ValueError(f"Skor kelayakan dari AI tidak valid: {skor_kelayakan}")
        
        skor_kelayakan = int(skor_kelayakan)
        if not (40 <= skor_kelayakan <= 95):
            logger.warning(f"⚠️ Skor kelayakan dari AI di luar range normal (40-95): {skor_kelayakan}. Tetap digunakan.")
        
        # Validasi estimasi balik modal
        estimasi_balik_modal = analysis_data["estimasi_balik_modal"]
        if not isinstance(estimasi_balik_modal, (int, float)):
            try:
                estimasi_balik_modal = int(float(str(estimasi_balik_modal).strip()))
            except (ValueError, TypeError):
                raise ValueError(f"Estimasi balik modal dari AI tidak valid: {estimasi_balik_modal}")
        
        estimasi_balik_modal = int(estimasi_balik_modal)
        if estimasi_balik_modal <= 0:
            raise ValueError(f"Estimasi balik modal dari AI harus positif: {estimasi_balik_modal}")
        
        # Validasi potensi pasar
        potensi_pasar = str(analysis_data["potensi_pasar"]).strip().upper()
        valid_potensi = ["TINGGI", "SEDANG", "RENDAH"]
        if potensi_pasar not in valid_potensi:
            logger.warning(f"⚠️ Potensi pasar dari AI tidak standar: {potensi_pasar}. Tetap digunakan.")
        
        # Validasi kesimpulan
        kesimpulan_ringkasan = str(analysis_data["kesimpulan_ringkasan"]).strip()
        if len(kesimpulan_ringkasan) < 50:
            logger.warning(f"⚠️ Kesimpulan dari AI terlalu pendek ({len(kesimpulan_ringkasan)} karakter). Tetap digunakan.")
        
        # Return semua nilai dari AI tanpa modifikasi apapun
        # PENTING: Semua nilai ini 100% berasal dari AI, tidak ada perhitungan manual
        return {
            "skor_kelayakan": skor_kelayakan,  # Dari AI
            "potensi_pasar": potensi_pasar,  # Dari AI
            "estimasi_balik_modal": estimasi_balik_modal,  # Dari AI
            "kesimpulan_ringkasan": kesimpulan_ringkasan  # Dari AI
        }

