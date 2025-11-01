import json
import logging
import random
from typing import Dict, Any
import google.generativeai as genai
from app.config import get_settings
from app.models.project import JenisIkan, Resiko

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure Gemini API
genai.configure(api_key=settings.apikey_gemini)

def analyze_project_with_gemini(
    project_name: str,
    jenis_ikan: JenisIkan,
    jumlah_team: int,
    modal: int,
    kabupaten_id: str,
    resiko: Resiko
) -> Dict[str, Any]:
    
    model = None
    model_used = None
    model_names = [
       # 'gemini-2.5-flash-lite',  # Coba format terbaru
        'gemini-2.5-pro',
        'gemini-1.5-flash',      # Fallback ke model flash
        'gemini-pro'              # Final fallback
    ]
    
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            model_used = model_name
            logger.info(f"✅ Menggunakan model: {model_name}")
            break
        except Exception as e:
            logger.warning(f"Model {model_name} tidak tersedia: {e}")
            continue
    
    if model is None:
        raise Exception("Tidak ada model Gemini yang tersedia. Pastikan API key valid dan model tersedia.")
    
    # Hitung skala project berdasarkan modal
    if modal < 30000000:
        skala = "Kecil"
        skala_multiplier = 0.9
    elif modal < 75000000:
        skala = "Menengah"
        skala_multiplier = 1.0
    elif modal < 150000000:
        skala = "Besar"
        skala_multiplier = 1.15
    else:
        skala = "Sangat Besar"
        skala_multiplier = 1.25
    
    # Faktor resiko - handle enum atau string
    resiko_value = resiko.value if hasattr(resiko, 'value') else str(resiko)
    resiko_multiplier = {
        "KONSERVATIF": 0.95,
        "MODERAT": 1.0,
        "AGRESIF": 1.1
    }.get(resiko_value, 1.0)
    
    # Faktor lokasi (beberapa kota/kabupaten di Sumbar)
    lokasi_faktor = {
        "Padang": 1.15,
        "Bukittinggi": 1.1,
        "Padang Panjang": 1.05,
        "Pariaman": 1.0,
        "Solok": 0.95,
        "Sawahlunto": 0.9,
        "Payakumbuh": 1.05
    }
    lokasi_multiplier = lokasi_faktor.get(kabupaten_id.title(), 1.0)
    
    # Faktor jenis ikan - handle enum atau string
    jenis_ikan_value = jenis_ikan.value if hasattr(jenis_ikan, 'value') else str(jenis_ikan)
    ikan_faktor = {
        "LELE": {"potensi": 1.15, "modal_adj": 1.0, "roi_months": 10},
        "NILA": {"potensi": 1.05, "modal_adj": 1.1, "roi_months": 14},
        "GURAME": {"potensi": 0.95, "modal_adj": 1.2, "roi_months": 16}
    }
    ikan_data = ikan_faktor.get(jenis_ikan_value, {"potensi": 1.0, "modal_adj": 1.0, "roi_months": 12})
    
    # Faktor team
    team_factor = 1.0 if jumlah_team == 1 else 1.05
    
    # Hitung estimasi modal realistis dengan variasi
    base_modal = modal
    adjusted_modal = int(base_modal * skala_multiplier * ikan_data["modal_adj"] * resiko_multiplier * lokasi_multiplier)
    # Tambahkan variasi random ±5%
    variation = random.uniform(0.95, 1.05)
    final_modal = int(adjusted_modal * variation)
    
    # Estimasi ROI berdasarkan jenis ikan dan skala
    base_roi = ikan_data["roi_months"]
    if skala == "Kecil":
        roi_adjust = random.uniform(1.0, 1.3)  # ROI lebih lama untuk skala kecil
    elif skala == "Besar":
        roi_adjust = random.uniform(0.8, 0.95)  # ROI lebih cepat untuk skala besar
    else:
        roi_adjust = random.uniform(0.9, 1.1)
    estimated_roi = int(base_roi * roi_adjust)
    
    # Hitung skor kelayakan dengan berbagai faktor
    base_score = 60
    score_modal = min(20, (modal / 100000000) * 20) if modal > 0 else 10
    score_lokasi = lokasi_multiplier * 10
    score_ikan = ikan_data["potensi"] * 10
    score_team = team_factor * 5
    score_resiko = {"KONSERVATIF": 10, "MODERAT": 8, "AGRESIF": 5}.get(resiko_value, 5)
    
    calculated_score = base_score + score_modal + score_lokasi + score_ikan + score_team + score_resiko
    final_score = min(95, max(40, int(calculated_score)))
    
    # Tentukan potensi pasar
    if lokasi_multiplier >= 1.1 and ikan_data["potensi"] >= 1.1:
        potensi_pasar = "TINGGI"
    elif lokasi_multiplier >= 1.0 and ikan_data["potensi"] >= 1.0:
        potensi_pasar = "SEDANG"
    else:
        potensi_pasar = "RENDAH"
    
    # Prompt untuk analisis dengan konteks lebih detail
    prompt = f"""
Anda adalah ahli analisis bisnis budidaya ikan profesional di Sumatera Barat dengan pengalaman 10+ tahun. Analisis project berikut dengan DETIL dan REALISTIS:

**Informasi Project:**
- Nama Project: {project_name}
- Jenis Ikan: {jenis_ikan_value}
- Jumlah Team: {jumlah_team} ({'Solo (dikelola sendiri)' if jumlah_team == 1 else f'Team ({jumlah_team} orang)'})
- Modal Awal: Rp {modal:,} (skala {skala.lower()})
- Lokasi: {kabupaten_id}, Sumatera Barat
- Resiko: {resiko_value}

**Analisis Faktor Spesifik:**

1. **Jenis Ikan {jenis_ikan_value}:**
   - PERTIMBANGKAN: Karakteristik budidaya {jenis_ikan_value}, waktu panen, harga jual pasar di Sumatera Barat
   - {jenis_ikan_value} di Sumatera Barat memiliki {'permintaan tinggi' if jenis_ikan_value == 'LELE' else 'permintaan sedang' if jenis_ikan_value == 'NILA' else 'permintaan khusus'} dari pasar lokal
   - Biaya produksi berbeda untuk setiap jenis ikan

2. **Lokasi {kabupaten_id}:**
   - EVALUASI: Akses pasar, infrastruktur, kondisi geografis, kompetisi di daerah tersebut
   - {kabupaten_id} memiliki {'akses pasar yang sangat baik' if lokasi_multiplier >= 1.1 else 'akses pasar yang baik' if lokasi_multiplier >= 1.0 else 'akses pasar terbatas'}
   - Pertimbangkan biaya operasional spesifik di {kabupaten_id}

3. **Skala Modal Rp {modal:,}:**
   - HITUNG REALISTIS: Berdasarkan skala {skala.lower()}, jenis ikan {jenis_ikan_value}, dan lokasi {kabupaten_id}
   - Modal ini {'cukup untuk' if modal >= 50000000 else 'terbatas untuk'} skala operasi yang efisien
   - Estimasi modal harus mencerminkan biaya aktual di {kabupaten_id} untuk jenis {jenis_ikan_value}

4. **Tim ({jumlah_team} orang):**
   - {'Dikelola solo memerlukan manajemen yang efisien' if jumlah_team == 1 else f'Tim {jumlah_team} orang memungkinkan pembagian tugas lebih optimal'}
   - Pertimbangkan overhead biaya tenaga kerja

5. **Resiko {resiko_value}:**
   - {'Resiko rendah dengan strategi konservatif' if resiko_value == 'KONSERVATIF' else 'Resiko sedang yang perlu dikelola' if resiko_value == 'MODERAT' else 'Resiko tinggi dengan potensi return tinggi'}

**OUTPUT yang DIPERLUKAN (JSON):**

Berdasarkan analisis DETIL di atas, berikan output JSON dengan:

{{
    "skor_kelayakan": <integer 40-95, HARUS BERBEDA berdasarkan kombinasi faktor-faktor di atas>,
    "potensi_pasar": "<TINGGI/SEDANG/RENDAH - HARUS SESUAI dengan evaluasi lokasi dan jenis ikan>",
    "estimasi_modal": <integer dalam rupiah, HARUS REALISTIS dan BERBEDA dari modal input berdasarkan skala, jenis ikan, dan lokasi. JANGAN SELALU 55 juta!>,
    "estimasi_balik_modal": <integer 8-24 bulan, HARUS BERBEDA berdasarkan jenis ikan, skala, dan strategi>,
    "kesimpulan_ringkasan": "<string penjelasan LENGKAP 300-500 karakter yang MENDALAM, menjelaskan MENGAPA skor kelayakan seperti itu, MENGAPA estimasi modal berbeda, MENGAPA potensi pasar seperti itu, dan REKOMENDASI SPESIFIK untuk project ini di {kabupaten_id}>"
}}

**KETENTUAN PENTING:**
1. **Skor Kelayakan (40-95):** HARUS BERBEDA dan mencerminkan kombinasi unik dari semua faktor. JANGAN SELALU 75!
   - Skor tinggi (80+): Modal besar + lokasi strategis + jenis ikan populer + tim memadai
   - Skor menengah (60-79): Kombinasi faktor yang seimbang
   - Skor rendah (40-59): Modal kecil + lokasi terpencil + jenis ikan kurang populer

2. **Estimasi Modal:** HARUS BERBEDA dan REALISTIS. Contoh variasi:
   - Modal kecil: 30-45 juta
   - Modal menengah: 50-70 juta  
   - Modal besar: 80-120 juta
   - Modal sangat besar: 130-180 juta
   JANGAN SELALU 55 JUTA!

3. **Estimasi Balik Modal:** HARUS BERBEDA berdasarkan jenis ikan dan skala
   - LELE: 8-12 bulan
   - NILA: 12-18 bulan
   - GURAME: 14-20 bulan

4. **Potensi Pasar:** Evaluasi REAL berdasarkan kombinasi lokasi + jenis ikan

5. **Kesimpulan:** HARUS SPESIFIK untuk project ini, bukan generic. Sebutkan {kabupaten_id}, {jenis_ikan_value}, skala modal, dan berikan analisis yang UNIK.

**CONTOH OUTPUT yang DICARI:**
- Jika modal kecil + lokasi terpencil: skor 50-60, estimasi modal mungkin 35-45 juta
- Jika modal besar + lokasi strategis: skor 85-95, estimasi modal mungkin 80-100 juta
- Variasikan berdasarkan kombinasi input!

Sekarang analisis project ini dengan DETIL dan berikan output JSON yang REALISTIS dan BERBEDA!
"""

    try:
        logger.info(f"🔍 Mengirim request ke Gemini API untuk analisis project: {project_name}")
        
        # Generate response dengan error handling
        try:
            response = model.generate_content(prompt)
        except Exception as api_err:
            logger.error(f"❌ Error saat memanggil Gemini API: {str(api_err)}")
            raise Exception(f"Error dari Gemini API: {str(api_err)}")
        
        # Extract text response - handle berbagai format response
        if not response:
            raise ValueError("Response dari Gemini API kosong atau None")
        
        # Handle berbagai tipe response dari Gemini
        if hasattr(response, 'text'):
            response_text = response.text
        elif hasattr(response, 'parts') and len(response.parts) > 0:
            # Jika response dalam format parts
            response_text = response.parts[0].text if hasattr(response.parts[0], 'text') else str(response.parts[0])
        elif isinstance(response, str):
            response_text = response
        else:
            # Coba convert ke string
            response_text = str(response)
        
        if not response_text:
            raise ValueError("Response text dari Gemini API kosong setelah extraction")
        
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
        
        # Remove leading/trailing whitespace dan newlines
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
        
        # Parse JSON
        try:
            analysis_data = json.loads(response_text)
        except json.JSONDecodeError as json_err:
            logger.error(f"❌ Error parsing JSON dari Gemini:")
            logger.error(f"Response text: {response_text[:1000]}")
            logger.error(f"JSON Error: {str(json_err)}")
            # Coba extract JSON menggunakan regex sebagai fallback
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    analysis_data = json.loads(json_match.group(0))
                    logger.info("✅ Berhasil extract JSON menggunakan regex fallback")
                except:
                    raise ValueError(f"Gagal parsing JSON dari Gemini API. Response tidak valid: {response_text[:200]}")
            else:
                raise ValueError(f"Tidak ditemukan JSON valid dalam response Gemini API: {response_text[:200]}")
        
        # Validasi dan normalisasi skor kelayakan (jangan terlalu generic)
        ai_score = int(analysis_data.get("skor_kelayakan", final_score))
        # Jika skor terlalu generik (70-75), gunakan calculated score dengan variasi
        if 70 <= ai_score <= 75:
            ai_score = final_score + random.randint(-5, 5)
            ai_score = min(95, max(40, ai_score))
        
        # Validasi estimasi modal (jangan selalu 55 juta)
        ai_modal = int(analysis_data.get("estimasi_modal", final_modal))
        # Jika estimasi modal terlalu dekat dengan 55 juta, gunakan calculated modal
        if 54000000 <= ai_modal <= 56000000 and abs(ai_modal - 55000000) < 2000000:
            ai_modal = final_modal
        
        # Validasi estimasi ROI
        ai_roi = int(analysis_data.get("estimasi_balik_modal", estimated_roi))
        
        logger.info(f"✅ Analisis berhasil: Skor {ai_score}/100, Modal: {ai_modal:,}, ROI: {ai_roi} bulan")
        
        # Validate dan normalize data
        return {
            "skor_kelayakan": ai_score,
            "potensi_pasar": analysis_data.get("potensi_pasar", potensi_pasar).upper(),
            "estimasi_modal": ai_modal,
            "estimasi_balik_modal": ai_roi,
            "kesimpulan_ringkasan": analysis_data.get("kesimpulan_ringkasan", "Analisis sedang diproses."),
            "ai_model_used": model_used,
            "ai_analysis_success": True
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parsing JSON dari Gemini: {e}")
        logger.error(f"Response text: {response_text}")
        raise ValueError(f"Gagal parsing response dari Gemini API: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Error calling Gemini API: {str(e)}")
        raise Exception(f"Gagal menganalisis project dengan Gemini API: {str(e)}")

