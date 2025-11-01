import logging
from sqlmodel import Session
from fastapi import HTTPException, status
from app.models.project import Project
from app.models.ringkasan_awal import RingkasanAwal, PotensiPasar
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectData, RingkasanAwalData, AIAnalysisInfo
from app.service.generative import analyze_project_with_gemini

logger = logging.getLogger(__name__)

def create_project_with_analysis(
    db: Session,
    project_data: ProjectCreate,
    user_id: str
) -> ProjectResponse:

    try:
        logger.info(f"🔍 Memulai analisis project: {project_data.project_name}")
        analysis_result = analyze_project_with_gemini(
            project_name=project_data.project_name,
            jenis_ikan=project_data.jenis_ikan,
            jumlah_team=project_data.jumlah_team,
            modal=project_data.modal,
            kabupaten_id=project_data.kabupaten_id,
            resiko=project_data.resiko
        )
        
        new_project = Project(
            project_name=project_data.project_name,
            user_id=user_id,
            kabupaten_id=project_data.kabupaten_id,
            jenis_ikan=project_data.jenis_ikan,
            jumlahTeam=project_data.jumlah_team,
            modal=project_data.modal,
            resiko=project_data.resiko
        )
        
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        
        
        new_ringkasan = RingkasanAwal(
            project_id=new_project.id,
            skor_kelayakan=analysis_result["skor_kelayakan"],
            potensi_pasar=PotensiPasar(analysis_result["potensi_pasar"]),
            estimasi_modal=analysis_result["estimasi_modal"],
            estimasi_balik_modal=analysis_result["estimasi_balik_modal"],
            kesimpulan_ringkasan=analysis_result["kesimpulan_ringkasan"]
        )
        
        db.add(new_ringkasan)
        db.commit()
        db.refresh(new_ringkasan)
        
    
        def get_enum_value(enum_obj):
            """Helper untuk mendapatkan value dari enum atau string"""
            if hasattr(enum_obj, 'value'):
                return enum_obj.value
            return str(enum_obj)
        
        project_response_data = ProjectData(
            id=new_project.id,
            project_name=new_project.project_name,
            jenis_ikan=get_enum_value(new_project.jenis_ikan),
            jumlah_team=new_project.jumlahTeam,
            modal=new_project.modal,
            kabupaten_id=new_project.kabupaten_id,
            resiko=get_enum_value(new_project.resiko),
            user_id=new_project.user_id
        )
        
        ai_model_used = analysis_result.get("ai_model_used", "unknown")
        ai_success = analysis_result.get("ai_analysis_success", False)
        
        ai_analysis_info = AIAnalysisInfo(
            status="success" if ai_success else "failed",
            model_used=ai_model_used,
            source="gemini",
            message=f"Analisis berhasil dilakukan menggunakan {ai_model_used}" if ai_success else "Analisis AI gagal"
        )
        
        ringkasan_response_data = RingkasanAwalData(
            skor_kelayakan=new_ringkasan.skor_kelayakan,
            potensi_pasar=get_enum_value(new_ringkasan.potensi_pasar),
            estimasi_modal=new_ringkasan.estimasi_modal,
            estimasi_balik_modal=new_ringkasan.estimasi_balik_modal,
            kesimpulan_ringkasan=new_ringkasan.kesimpulan_ringkasan,
            ai_analysis=ai_analysis_info
        )
        
        return ProjectResponse(
            success=True,
            message="Project berhasil dibuat dan dianalisis",
            data=project_response_data,
            ringkasan_awal=ringkasan_response_data
        )
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error dalam analisis AI: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Error creating project: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal membuat project: {str(e)}"
        )

