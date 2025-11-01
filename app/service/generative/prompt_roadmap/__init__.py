from app.service.generative.prompt_roadmap.analyzer import RoadmapAnalyzer

def generate_roadmap_with_gemini(
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
):
    """Helper function untuk generate roadmap dengan Gemini"""
    analyzer = RoadmapAnalyzer()
    return analyzer.generate_roadmap(
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
        analisis_financial=analisis_financial,
        lang=lang,
        lat=lat
    )

