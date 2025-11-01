from app.models.project import JenisIkan, Resiko
from app.models.ringkasan_awal import PotensiPasar

class PromptBuilder:
    """Kelas untuk membangun prompt roadmap"""
    
    @staticmethod
    def build_roadmap_prompt(
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
        analisis_financial: dict,
        lang: float = None,
        lat: float = None
    ) -> str:
        """Membangun prompt untuk generate roadmap"""
        
        # Extract info dari informasi_teknis dan analisis_financial
        kolam_info = informasi_teknis.get("spesifikasiKolam", {})
        benih_info = informasi_teknis.get("spesifikasiBenih", {})
        pakan_info = informasi_teknis.get("spesifikasiPakan", {})
        siklus_info = analisis_financial.get("analisisROI", {})
        lama_siklus = siklus_info.get("lamaSiklus", "2.5 bulan")
        
        return f"""
Anda adalah ahli budidaya ikan profesional dengan pengalaman 15+ tahun. Berdasarkan informasi project, informasi teknis, dan analisis financial berikut, buatkan roadmap/langkah-langkah budidaya yang DETIL dan REALISTIS:

**Informasi Project:**
- Nama Project: {project_name}
- Jenis Ikan: {jenis_ikan}
- Modal Awal: Rp {modal:,}
- Lokasi: {kabupaten_id}, Sumatera Barat{f' (Koordinat: {lat}, {lang})' if lang and lat else ''}
- Resiko: {resiko}
- Skor Kelayakan: {skor_kelayakan}/100
- Potensi Pasar: {potensi_pasar}
- Estimasi Balik Modal: {estimasi_balik_modal} bulan
- Lama Siklus: {lama_siklus}

**Informasi Teknis:**
- Kolam: {kolam_info.get('jenis', 'N/A')}, {kolam_info.get('ukuran', 'N/A')}, {kolam_info.get('jumlahKolam', 'N/A')} unit
- Benih: {benih_info.get('jenis', 'N/A')}, {benih_info.get('jumlah', 'N/A')} ekor, ukuran {benih_info.get('ukuran', 'N/A')}
- Pakan: {pakan_info.get('jenis', 'N/A')}, protein {pakan_info.get('protein', 'N/A')}, frekuensi {pakan_info.get('frekuensiPemberian', 'N/A')}
- Kualitas Air: pH {informasi_teknis.get('kualitasAir', {}).get('pH', 'N/A')}, suhu {informasi_teknis.get('kualitasAir', {}).get('suhu', 'N/A')}

**Tugas Anda:**
Buatkan roadmap/langkah-langkah budidaya {jenis_ikan} yang DETIL, REALISTIS, dan SESUAI dengan informasi teknis yang sudah ditetapkan. Roadmap harus mencakup semua tahapan dari persiapan hingga panen dengan estimasi waktu yang realistis.

**OUTPUT yang DIPERLUKAN (JSON) - format dinamis tapi struktur konsisten:**

Roadmap harus berisi langkah-langkah yang detail dengan estimasi waktu. Buatkan langkah-langkah yang SPESIFIK dan PRAKTIS untuk project ini.

Format JSON:
{{
    "response": {{
        "judul": "<judul roadmap, contoh: Roadmap Budidaya {jenis_ikan} {lama_siklus}>",
        "detail": "<deskripsi singkat roadmap>",
        "list": [
            {{
                "step": <nomor step, mulai dari 1>,
                "title": "<judul step, contoh: Persiapan Kolam>",
                "deskripsi": "<deskripsi lengkap langkah-langkah yang harus dilakukan, minimal 2-3 kalimat, SPESIFIK untuk project ini>"
            }},
            {{
                "step": <nomor step berikutnya>,
                "title": "<judul step>",
                "deskripsi": "<deskripsi lengkap>"
            }}
            // ... lanjutkan untuk semua step hingga panen
        ]
    }},
    "request": null,
    "step": 1,
    "isRequest": false,
    "roadmapId": null
}}

**KETENTUAN PENTING:**
1. Buatkan minimal 5-8 langkah yang mencakup: Persiapan, Pengisian Air, Tebar Benih, Manajemen Pakan, Monitoring, Panen
2. Setiap langkah harus SPESIFIK dan disesuaikan dengan informasi teknis yang sudah ada
3. Deskripsi harus DETIL dan PRAKTIS (minimal 2-3 kalimat per step)
4. Step harus berurutan dari persiapan hingga panen
5. Estimasi waktu harus realistis sesuai lama siklus {lama_siklus}
6. Judul roadmap harus sesuai dengan jenis ikan dan lama siklus
7. Response harus dalam format JSON yang valid

**Contoh struktur step yang diperlukan:**
- Step 1: Persiapan Kolam (bersihkan, pasang terpal, dll sesuai jenis kolam)
- Step 2: Pengisian Air & Setting Kualitas (atur pH, suhu, kejernihan sesuai spesifikasi)
- Step 3: Tebar Benih (sesuai jumlah dan ukuran benih)
- Step 4: Manajemen Pakan (sesuai frekuensi dan rasio pakan)
- Step 5: Monitoring Harian (sesuai parameter kualitas air)
- Step 6: Manajemen Kesehatan (sesuai spesifikasi manajemen kesehatan)
- Step 7: Panen (sesuai estimasi berat panen dan waktu panen)

Sekarang buatkan roadmap yang DETIL dan REALISTIS untuk project ini!
"""

