import logging
import json
import re
from typing import Dict, Any
from app.service.generative.prompt_roadmap.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class SubStepGenerator:
    """Service untuk generate sub-step dari user request menggunakan Gemini AI"""
    
    def __init__(self):
        self.client = GeminiClient()
    
    def generate_substep_from_request(
        self,
        user_request: str,
        parent_step_title: str,
        parent_step_deskripsi: str,
        project_name: str,
        jenis_ikan: str,
        informasi_teknis: dict = None
    ) -> Dict[str, Any]:
        """Generate title dan deskripsi sub-step dari user request menggunakan AI"""
        
        prompt = f"""
Anda adalah ahli budidaya ikan profesional. User memberikan masukkan/request untuk detail lebih lanjut dari langkah berikut:

**Parent Step:**
- Judul: {parent_step_title}
- Deskripsi: {parent_step_deskripsi}

**Project Info:**
- Nama Project: {project_name}
- Jenis Ikan: {jenis_ikan}

**Request/Input dari User:**
{user_request}

**Tugas Anda:**
Berdasarkan request/masukkan user di atas, buatkan sub-step yang DETIL dan PRAKTIS. Sub-step ini adalah detail/elaborasi dari parent step berdasarkan masukkan user.

**OUTPUT yang DIPERLUKAN (JSON):**
{{
    "title": "<judul sub-step yang singkat, jelas, dan sesuai dengan request user (maksimal 50 karakter)>",
    "deskripsi": "<deskripsi lengkap sub-step minimal 50 karakter yang DETIL dan PRAKTIS, menjelaskan langkah-langkah spesifik berdasarkan request user>"
}}

**KETENTUAN PENTING:**
1. Title harus SINGKAT, JELAS, dan mencerminkan request user
2. Deskripsi harus DETIL, PRAKTIS, dan minimal 50 karakter
3. Sub-step harus relevan dengan parent step
4. Gunakan bahasa yang mudah dipahami
5. Berikan instruksi yang SPESIFIK dan dapat dijalankan

Sekarang buatkan sub-step berdasarkan request user di atas!
"""
        
        logger.info(f"🔍 Mengirim request ke Gemini API untuk generate sub-step dari user request")
        
        try:
            response = self.client.generate_content(prompt)
        except Exception as api_err:
            logger.error(f"❌ Error saat memanggil Gemini API: {str(api_err)}")
            raise Exception(f"Error dari Gemini API: {str(api_err)}")
        
        # Extract response text
        if hasattr(response, 'text'):
            response_text = response.text
        elif hasattr(response, 'parts') and len(response.parts) > 0:
            response_text = response.parts[0].text if hasattr(response.parts[0], 'text') else str(response.parts[0])
        else:
            response_text = str(response)
        
        if not response_text:
            raise ValueError("Response text dari Gemini API kosong")
        
        # Clean response
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Extract JSON
        if "{" in response_text and "}" in response_text:
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            response_text = response_text[start_idx:end_idx]
        
        # Parse JSON
        try:
            substep_data = json.loads(response_text)
        except json.JSONDecodeError as json_err:
            logger.error(f"❌ Error parsing JSON: {str(json_err)}")
            logger.error(f"Response text: {response_text[:500]}")
            
            # Fallback: extract using regex
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    substep_data = json.loads(json_match.group(0))
                except:
                    raise ValueError(f"Gagal parsing JSON dari Gemini API: {response_text[:200]}")
            else:
                raise ValueError(f"Tidak ditemukan JSON valid dalam response: {response_text[:200]}")
        
        # Validate
        if "title" not in substep_data or not substep_data["title"]:
            raise ValueError("Title tidak ditemukan dalam response AI")
        
        if "deskripsi" not in substep_data or not substep_data["deskripsi"]:
            raise ValueError("Deskripsi tidak ditemukan dalam response AI")
        
        if len(substep_data["deskripsi"]) < 20:
            logger.warning(f"⚠️ Deskripsi terlalu pendek ({len(substep_data['deskripsi'])} karakter)")
        
        logger.info(f"✅ Sub-step berhasil di-generate: {substep_data['title']}")
        
        return {
            "title": substep_data["title"].strip(),
            "deskripsi": substep_data["deskripsi"].strip()
        }

