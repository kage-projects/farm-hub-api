from app.service.generative.prompt_analisis_financial.analyzer import AnalisisFinancialAnalyzer

def generate_analisis_financial_with_gemini(
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
):
    """Helper function untuk generate analisis financial dengan Gemini"""
    analyzer = AnalisisFinancialAnalyzer()
    return analyzer.generate_analisis_financial(
        project_name=project_name,
        jenis_ikan=jenis_ikan,
        modal=modal,
        kabupaten_id=kabupaten_id,
        resiko=resiko,
        skor_kelayakan=skor_kelayakan,
        potensi_pasar=potensi_pasar,
        estimasi_balik_modal=estimasi_balik_modal,
        kesimpulan_ringkasan=kesimpulan_ringkasan,
        informasi_teknis=informasi_teknis,
        lang=lang,
        lat=lat
    )

