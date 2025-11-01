from app.service.generative.prompt_informasi_teknis.analyzer import InformasiTeknisAnalyzer

def generate_informasi_teknis_with_gemini(
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
):
    """Helper function untuk generate informasi teknis dengan Gemini"""
    analyzer = InformasiTeknisAnalyzer()
    return analyzer.generate_informasi_teknis(
        project_name=project_name,
        jenis_ikan=jenis_ikan,
        modal=modal,
        kabupaten_id=kabupaten_id,
        resiko=resiko,
        skor_kelayakan=skor_kelayakan,
        potensi_pasar=potensi_pasar,
        estimasi_balik_modal=estimasi_balik_modal,
        kesimpulan_ringkasan=kesimpulan_ringkasan,
        lang=lang,
        lat=lat
    )
