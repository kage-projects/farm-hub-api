import json
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ResponseParser:
    """Kelas untuk parsing dan validasi response dari Gemini API untuk roadmap"""
    
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
    def validate_and_normalize_roadmap(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validasi dan normalisasi data roadmap dari AI"""
        
        if "response" not in analysis_data:
            raise ValueError("Field 'response' tidak ditemukan dalam response AI")
        
        if not isinstance(analysis_data["response"], dict):
            raise ValueError("Field 'response' harus berupa object/dictionary")
        
        response = analysis_data["response"]
        
        # Validasi required fields di response
        required_response_fields = ["judul", "detail", "list"]
        for field in required_response_fields:
            if field not in response:
                raise ValueError(f"Field response.{field} tidak ditemukan")
        
        # Validasi list harus array
        if not isinstance(response["list"], list):
            raise ValueError("Field response.list harus berupa array")
        
        # Validasi minimal ada 5 step
        if len(response["list"]) < 5:
            logger.warning(f"⚠️ Roadmap hanya memiliki {len(response['list'])} step, disarankan minimal 5 step")
        
        # Validasi setiap step dalam list
        for idx, step in enumerate(response["list"]):
            if not isinstance(step, dict):
                raise ValueError(f"Step {idx + 1} harus berupa object/dictionary")
            
            required_step_fields = ["step", "title", "deskripsi"]
            for field in required_step_fields:
                if field not in step:
                    raise ValueError(f"Field list[{idx}].{field} tidak ditemukan")
            
            if not isinstance(step["step"], (int, float)):
                try:
                    step["step"] = float(step["step"])
                except (ValueError, TypeError):
                    raise ValueError(f"Field list[{idx}].step harus berupa number")
            
            if not isinstance(step["title"], str) or len(step["title"].strip()) == 0:
                raise ValueError(f"Field list[{idx}].title harus berupa string yang tidak kosong")
            
            if not isinstance(step["deskripsi"], str) or len(step["deskripsi"].strip()) < 20:
                logger.warning(f"⚠️ Step {idx + 1} deskripsi terlalu pendek (disarankan minimal 20 karakter)")
        
        # Set default values untuk fields luar response jika tidak ada
        # Pastikan step adalah float untuk konsistensi dengan model
        step_value = analysis_data.get("step", 1.0)
        if not isinstance(step_value, (int, float)):
            try:
                step_value = float(step_value)
            except (ValueError, TypeError):
                step_value = 1.0
        else:
            step_value = float(step_value)
        
        normalized_data = {
            "response": response,
            "request": analysis_data.get("request", None),
            "step": step_value,
            "isRequest": analysis_data.get("isRequest", False),
            "roadmapId": analysis_data.get("roadmapId", None)
        }
        
        return normalized_data

