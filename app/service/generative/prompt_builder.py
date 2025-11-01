from app.models.project import JenisIkan, Resiko

class PromptBuilder:
    """Kelas untuk membangun prompt analisis project - Semua hasil harus dari AI, tidak ada perhitungan manual"""
    
    @staticmethod
    def build_analysis_prompt(
        project_name: str,
        jenis_ikan: JenisIkan,
        modal: int,
        kabupaten_id: str,
        resiko: Resiko,
        skala: str,
        lokasi_multiplier: float,
        ikan_data: dict,
        lang: float = None,
        lat: float = None
    ) -> str:
        """Membangun prompt untuk analisis project"""
        
        fish_demand_map = {
            'LELE': 'permintaan tinggi',
            'NILA': 'permintaan sedang',
            'GURAME': 'permintaan khusus'
        }
        fish_demand = fish_demand_map.get(jenis_ikan.value, 'permintaan sedang')
        
        location_access = (
            'akses pasar yang sangat baik' if lokasi_multiplier >= 1.1 
            else 'akses pasar yang baik' if lokasi_multiplier >= 1.0 
            else 'akses pasar terbatas'
        )
        
        risk_description = {
            'KONSERVATIF': 'Resiko rendah dengan strategi konservatif',
            'MODERAT': 'Resiko sedang yang perlu dikelola',
            'AGRESIF': 'Resiko tinggi dengan potensi return tinggi'
        }.get(resiko.value, 'Resiko sedang yang perlu dikelola')
        
        modal_adequacy = 'cukup untuk' if modal >= 50000000 else 'terbatas untuk'
        
        return f"""
Anda adalah ahli analisis bisnis budidaya ikan profesional di Sumatera Barat dengan pengalaman 10+ tahun. Analisis project berikut dengan DETIL dan REALISTIS:

**Informasi Project:**
- Nama Project: {project_name}
- Jenis Ikan: {jenis_ikan.value}
- Modal Awal: Rp {modal:,} (skala {skala.lower()})
- Lokasi: {kabupaten_id}, Sumatera Barat{f' (Koordinat: {lat}, {lang})' if lang and lat else ''}
- Resiko: {resiko.value}

**Analisis Faktor Spesifik:**

1. **Jenis Ikan {jenis_ikan.value}:**
   - PERTIMBANGKAN: Karakteristik budidaya {jenis_ikan.value}, waktu panen, harga jual pasar di Sumatera Barat
   - {jenis_ikan.value} di Sumatera Barat memiliki {fish_demand} dari pasar lokal
   - Biaya produksi berbeda untuk setiap jenis ikan

2. **Lokasi {kabupaten_id}:**
   - EVALUASI: Akses pasar, infrastruktur, kondisi geografis, kompetisi di daerah tersebut
   - {kabupaten_id} memiliki {location_access}
   - Pertimbangkan biaya operasional spesifik di {kabupaten_id}

3. **Skala Modal Rp {modal:,}:**
   - EVALUASI: Berdasarkan skala {skala.lower()}, jenis ikan {jenis_ikan.value}, dan lokasi {kabupaten_id}
   - Modal ini {modal_adequacy} skala operasi yang efisien

4. **Resiko {resiko.value}:**
   - {risk_description}

**OUTPUT yang DIPERLUKAN (JSON) - WAJIB SEMUA FIELD:**

Berdasarkan analisis DETIL di atas, berikan output JSON dengan SEMUA field berikut (JANGAN ADA YANG KOSONG):

{{
    "skor_kelayakan": <integer 40-95, WAJIB ADA, HARUS BERBEDA berdasarkan kombinasi faktor-faktor di atas>,
    "potensi_pasar": "<TINGGI/SEDANG/RENDAH, WAJIB ADA, HARUS SESUAI dengan evaluasi lokasi dan jenis ikan>",
    "estimasi_balik_modal": <integer 8-24 bulan, WAJIB ADA, HARUS BERBEDA berdasarkan jenis ikan, skala, dan strategi>,
    "kesimpulan_ringkasan": "<string penjelasan LENGKAP minimal 300 karakter, WAJIB ADA, yang MENDALAM, menjelaskan MENGAPA skor kelayakan seperti itu, MENGAPA potensi pasar seperti itu, dan REKOMENDASI SPESIFIK untuk project ini di {kabupaten_id}>"
}}

**PENTING:** Semua field di atas WAJIB diberikan dan TIDAK BOLEH NULL atau KOSONG. Jika ada field yang tidak bisa ditentukan, tetap berikan nilai terbaik berdasarkan analisis Anda.

**KETENTUAN PENTING:**
1. **Skor Kelayakan (40-95):** HARUS BERBEDA dan mencerminkan kombinasi unik dari semua faktor. JANGAN SELALU 75!
   - Skor tinggi (80+): Modal besar + lokasi strategis + jenis ikan populer
   - Skor menengah (60-79): Kombinasi faktor yang seimbang
   - Skor rendah (40-59): Modal kecil + lokasi terpencil + jenis ikan kurang populer

2. **Estimasi Balik Modal:** HARUS BERBEDA berdasarkan jenis ikan dan skala
   - LELE: 8-12 bulan
   - NILA: 12-18 bulan
   - GURAME: 14-20 bulan

4. **Potensi Pasar:** Evaluasi REAL berdasarkan kombinasi lokasi + jenis ikan

5. **Kesimpulan:** HARUS SPESIFIK untuk project ini, bukan generic. Sebutkan {kabupaten_id}, {jenis_ikan.value}, skala modal, dan berikan analisis yang UNIK.

**CONTOH OUTPUT yang DICARI:**
- Jika modal kecil + lokasi terpencil: skor 50-60
- Jika modal besar + lokasi strategis: skor 85-95
- Variasikan berdasarkan kombinasi input!

Sekarang analisis project ini dengan DETIL dan berikan output JSON yang REALISTIS dan BERBEDA!
"""

