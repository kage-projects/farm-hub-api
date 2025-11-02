from app.models.project import JenisIkan, Resiko
from app.models.ringkasan_awal import PotensiPasar

class PromptBuilder:
    """Kelas untuk membangun prompt analisis financial"""
    
    @staticmethod
    def build_analisis_financial_prompt(
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
    ) -> str:
        
        kolam_info = informasi_teknis.get("spesifikasiKolam", {})
        benih_info = informasi_teknis.get("spesifikasiBenih", {})
        
        return f"""
Anda adalah ahli analisis financial budidaya ikan profesional dengan pengalaman 15+ tahun. Berdasarkan informasi project dan informasi teknis berikut, buatkan analisis financial yang DETIL dan REALISTIS:

**Informasi Project:**
- Nama Project: {project_name}
- Jenis Ikan: {jenis_ikan}
- Modal Awal: Rp {modal:,}
- Lokasi: {kabupaten_id}, Sumatera Barat{f' (Koordinat: {lat}, {lang})' if lang and lat else ''}
- Resiko: {resiko}
- Skor Kelayakan: {skor_kelayakan}/100
- Potensi Pasar: {potensi_pasar}
- Estimasi Balik Modal: {estimasi_balik_modal} bulan
- Kesimpulan: {kesimpulan_ringkasan}

**Informasi Teknis (untuk referensi):**
- Kolam: {kolam_info.get('jenis', 'N/A')}, {kolam_info.get('ukuran', 'N/A')}, {kolam_info.get('jumlahKolam', 'N/A')} unit
- Benih: {benih_info.get('jenis', 'N/A')}, {benih_info.get('jumlah', 'N/A')} ekor
- Volume Air: {kolam_info.get('volumeAir', 'N/A')}

**Tugas Anda:**
Buatkan analisis financial lengkap untuk budidaya {jenis_ikan} dengan modal Rp {modal:,} di {kabupaten_id}. Analisis harus REALISTIS, DETIL, dan SESUAI dengan skala modal serta informasi teknis yang sudah ditetapkan.

**OUTPUT yang DIPERLUKAN (JSON) - WAJIB SEMUA FIELD dengan format camelCase:**

{{
    "rincianModalAwal": {{
        "kolamTerpal": <biaya kolam terpal dalam rupiah (jika menggunakan terpal)>,
        "pompaAir": <biaya pompa air dalam rupiah>,
        "selangFilter": <biaya selang dan filter dalam rupiah>,
        "pembelianBenih": <biaya pembelian benih berdasarkan jumlah dan harga pasar>,
        "totalModalAwal": <total semua biaya modal awal, HARUS MENDEKATI modal Rp {modal:,}>
    }},
    "biayaOperasional": {{
        "pakanBulanan": <biaya pakan per bulan berdasarkan jumlah benih dan kebutuhan pakan>,
        "listrik": <biaya listrik per bulan untuk pompa dan peralatan>,
        "vitaminObat": <biaya vitamin dan obat per bulan>,
        "lainnya": <biaya operasional lain-lain per bulan>,
        "totalOperasionalBulanan": <total biaya operasional per bulan>
    }},
    "analisisROI": {{
        "investasiAwal": <sama dengan totalModalAwal>,
        "proyeksiKeuntunganPerSiklus": <proyeksi keuntungan per siklus panen berdasarkan harga jual dan biaya>,
        "roi": "<ROI dalam persen, contoh: 67.30%>",
        "lamaSiklus": "<lama satu siklus budidaya dalam bulan, contoh: 2.5 bulan>"
    }},
    "analisisBEP": {{
        "modalAwal": <sama dengan totalModalAwal>,
        "marginPerSiklus": <margin keuntungan per siklus>,
        "breakEvenPoint": "<break even point dalam jumlah siklus, contoh: 1.5 siklus>"
    }},
    "proyeksiPendapatan": {{
        "panenPerSiklusKg": <berat panen per siklus dalam kg, berdasarkan jumlah benih dan survival rate>,
        "hargaPerKg": <harga jual per kg berdasarkan harga pasar {jenis_ikan} di Sumatera Barat>,
        "pendapatanPerPanen": <total pendapatan per panen (panenPerSiklusKg x hargaPerKg)>
    }}
}}

**KETENTUAN PENTING:**
1. Semua nilai biaya harus REALISTIS dan SESUAI dengan modal Rp {modal:,}
2. totalModalAwal harus MENDEKATI modal project (dalam range 85-100% dari modal)
3. Hitung proyeksi panen berdasarkan jumlah benih dan survival rate realistis untuk {jenis_ikan}
4. Harga jual harus sesuai dengan harga pasar {jenis_ikan} di Sumatera Barat
5. ROI dan BEP harus realistis berdasarkan estimasi_balik_modal ({estimasi_balik_modal} bulan)
6. Lama siklus harus sesuai dengan karakteristik {jenis_ikan}
7. Gunakan format camelCase untuk semua key JSON
8. Jangan ada field yang kosong atau null

**Rumus yang harus digunakan:**
- Survival rate {jenis_ikan}: 80-90% (realistis)
- Margin: pendapatan - (modal awal + biaya operasional per siklus)
- ROI: (keuntungan per siklus / investasi awal) x 100%
- BEP: modal awal / margin per siklus

Sekarang buatkan analisis financial yang DETIL dan REALISTIS untuk project ini!
"""

