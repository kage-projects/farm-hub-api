from app.models.project import JenisIkan, Resiko
from app.models.ringkasan_awal import PotensiPasar

class PromptBuilder:
    """Kelas untuk membangun prompt informasi teknis"""
    
    @staticmethod
    def build_informasi_teknis_prompt(
        project_name: str,
        jenis_ikan: str,
        modal: int,
        kabupaten_id: str,
        resiko: str,
        skor_kelayakan: int,
        potensi_pasar: str,
        estimasi_balik_modal: int,
        kesimpulan_ringkasan: str,
        lang: float = None,
        lat: float = None
    ) -> str:
        """Membangun prompt untuk generate informasi teknis"""
        
        return f"""
Anda adalah ahli budidaya ikan profesional dengan pengalaman 15+ tahun. Berdasarkan informasi project berikut, buatkan informasi teknis yang DETIL dan REALISTIS untuk budidaya ikan {jenis_ikan}:

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

**Tugas Anda:**
Buatkan informasi teknis lengkap untuk budidaya {jenis_ikan} dengan modal Rp {modal:,} di {kabupaten_id}. Informasi harus REALISTIS, DETIL, dan SESUAI dengan skala modal dan karakteristik {jenis_ikan}.

**OUTPUT yang DIPERLUKAN (JSON) - WAJIB SEMUA FIELD dengan format camelCase:**

{{
    "spesifikasiKolam": {{
        "jenis": "<jenis kolam yang sesuai untuk {jenis_ikan} dan modal Rp {modal:,}, contoh: Kolam Terpal, Kolam Beton, Kolam Tanah>",
        "ukuran": "<ukuran kolam dalam format: panjang x lebar x tinggi, contoh: 3m x 4m x 1m>",
        "volumeAir": "<volume air dalam liter, contoh: 10.000 liter>",
        "jumlahKolam": <jumlah kolam yang realistis berdasarkan modal>,
        "kedalamanAir": "<kedalaman air optimal untuk {jenis_ikan}, dalam cm>"
    }},
    "kualitasAir": {{
        "pH": "<range pH optimal untuk {jenis_ikan}, contoh: 6.5 - 8.0>",
        "suhu": "<range suhu optimal dalam derajat celcius, contoh: 27 - 30 C>",
        "oksigenTerlarut": "<kadar oksigen terlarut optimal dalam mg/L, contoh: 3 - 5 mg/L>",
        "kejernihan": "<kejernihan air optimal dalam cm, contoh: 30 - 40 cm>"
    }},
    "spesifikasiBenih": {{
        "jenis": "<jenis/strain benih {jenis_ikan} yang direkomendasikan, contoh: Lele Sangkuriang, Nila NIRWANA>",
        "ukuran": "<ukuran benih saat tebar dalam cm, contoh: 5 - 7 cm>",
        "jumlah": <jumlah benih total yang realistis berdasarkan ukuran kolam>,
        "padatTebar": "<padat tebar dalam ekor/m2, contoh: 200 ekor/m2>"
    }},
    "spesifikasiPakan": {{
        "jenis": "<jenis pakan yang direkomendasikan, contoh: Pelet Terapung, Pelet Tenggelam>",
        "protein": "<kandungan protein optimal dalam persen, contoh: 30% - 32%>",
        "frekuensiPemberian": "<frekuensi pemberian pakan per hari, contoh: 3x sehari>",
        "rasioPakan": "<rasio pakan terhadap bobot biomass dalam persen, contoh: 3% dari bobot biomass>"
    }},
    "manajemenKesehatan": {{
        "cekRutin": "<frekuensi pengecekan kesehatan ikan, contoh: 2x seminggu>",
        "vaksin": <boolean, apakah perlu vaksin atau tidak>,
        "penangananHama": "<cara penanganan hama/penyakit yang direkomendasikan>",
        "pencegahanPenyakit": "<tindakan pencegahan penyakit yang harus dilakukan>"
    }},
    "teknologiPendukung": {{
        "sensorPH": <boolean, apakah direkomendasikan menggunakan sensor pH>,
        "otomatisasiPakan": <boolean, apakah direkomendasikan otomatisasi pakan>,
        "sistemMonitoring": "<jenis sistem monitoring yang direkomendasikan berdasarkan modal, contoh: IoT Basic Monitoring, Manual Monitoring>",
        "kameraKolam": <boolean, apakah direkomendasikan kamera untuk monitoring>
    }}
}}

**KETENTUAN PENTING:**
1. Semua nilai harus REALISTIS dan SESUAI dengan modal Rp {modal:,} dan jenis ikan {jenis_ikan}
2. Ukuran kolam dan jumlah kolam harus proporsional dengan modal
3. Spesifikasi teknis harus sesuai dengan karakteristik {jenis_ikan}
4. Teknologi pendukung harus realistis sesuai budget (jangan over-spec untuk modal kecil)
5. Gunakan format camelCase untuk semua key JSON
6. Jangan ada field yang kosong atau null

Sekarang buatkan informasi teknis yang DETIL dan REALISTIS untuk project ini!
"""

