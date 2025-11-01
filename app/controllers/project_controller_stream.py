import json
import logging
from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.project import Project
from app.models.ringkasan_awal import RingkasanAwal, PotensiPasar
from app.schemas.project import ProjectCreate, ProjectData, RingkasanAwalData, AIAnalysisInfo
from app.service.generative.prompt_ringkasan_awal.project_analyzer import ProjectAnalyzer

logger = logging.getLogger(__name__)

def create_project_with_streaming(
    db: Session,
    project_data: ProjectCreate,
    user_id: str
):
    """Create project dengan streaming response dari AI analysis
    
    Generator function yang yield Server-Sent Events (SSE) format
    """
    try:
        # Generate project name jika tidak diisi
        project_name = project_data.project_name
        if not project_name:
            project_name = f"Project {project_data.jenis_ikan.value} - {project_data.kabupaten_id}"
        
        analyzer = ProjectAnalyzer()
        
        full_result = None
        for chunk in analyzer.analyze_project_stream(
            project_name=project_name,
            jenis_ikan=project_data.jenis_ikan,
            modal=project_data.modal,
            kabupaten_id=project_data.kabupaten_id,
            resiko=project_data.resiko,
            lang=project_data.lang,
            lat=project_data.lat
        ):
            # Forward semua chunks ke client
            chunk_json = json.dumps(chunk, ensure_ascii=False)
            yield f"data: {chunk_json}\n\n"
            
            # Simpan result untuk digunakan setelah streaming selesai
            if chunk.get("type") == "result":
                full_result = chunk.get("data")
            elif chunk.get("type") == "error":
                # Jika ada error, stop streaming
                db.rollback()
                return
        
        if not full_result:
            raise ValueError("Tidak ada hasil dari analisis AI")
        
        # Setelah streaming selesai, simpan ke database
        yield f"data: {json.dumps({'type': 'status', 'message': 'Menyimpan data ke database...', 'progress': 95}, ensure_ascii=False)}\n\n"
        
        # Create project
        new_project = Project(
            project_name=project_name,
            user_id=user_id,
            kabupaten_id=project_data.kabupaten_id,
            jenis_ikan=project_data.jenis_ikan,
            modal=project_data.modal,
            resiko=project_data.resiko,
            lang=project_data.lang,
            lat=project_data.lat
        )
        
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        
        # Create ringkasan awal
        new_ringkasan = RingkasanAwal(
            project_id=new_project.id,
            skor_kelayakan=full_result["skor_kelayakan"],
            potensi_pasar=PotensiPasar(full_result["potensi_pasar"]),
            estimasi_balik_modal=full_result["estimasi_balik_modal"],
            kesimpulan_ringkasan=full_result["kesimpulan_ringkasan"]
        )
        
        db.add(new_ringkasan)
        db.commit()
        db.refresh(new_ringkasan)
        
        # Helper function
        def get_enum_value(enum_obj):
            if hasattr(enum_obj, 'value'):
                return enum_obj.value
            return str(enum_obj)
        
        # Prepare final response
        project_response_data = ProjectData(
            id=new_project.id,
            project_name=new_project.project_name,
            jenis_ikan=get_enum_value(new_project.jenis_ikan),
            modal=new_project.modal,
            kabupaten_id=new_project.kabupaten_id,
            resiko=get_enum_value(new_project.resiko),
            user_id=new_project.user_id,
            lang=new_project.lang,
            lat=new_project.lat
        )
        
        ai_analysis_info = AIAnalysisInfo(
            status="success",
            model_used=full_result.get("ai_model_used", "unknown"),
            source="gemini",
            message=f"Analisis berhasil dilakukan menggunakan {full_result.get('ai_model_used', 'unknown')}"
        )
        
        ringkasan_response_data = RingkasanAwalData(
            skor_kelayakan=new_ringkasan.skor_kelayakan,
            potensi_pasar=get_enum_value(new_ringkasan.potensi_pasar),
            estimasi_balik_modal=new_ringkasan.estimasi_balik_modal,
            kesimpulan_ringkasan=new_ringkasan.kesimpulan_ringkasan,
            ai_analysis=ai_analysis_info
        )
        
        # Send final complete response
        final_response = {
            "type": "completed",
            "success": True,
            "message": "Project berhasil dibuat dan dianalisis",
            "data": {
                "id": project_response_data.id,
                "project_name": project_response_data.project_name,
                "jenis_ikan": project_response_data.jenis_ikan,
                "modal": project_response_data.modal,
                "kabupaten_id": project_response_data.kabupaten_id,
                "resiko": project_response_data.resiko,
                "user_id": project_response_data.user_id,
                "lang": project_response_data.lang,
                "lat": project_response_data.lat
            },
            "ringkasan_awal": {
                "skor_kelayakan": ringkasan_response_data.skor_kelayakan,
                "potensi_pasar": ringkasan_response_data.potensi_pasar,
                "estimasi_balik_modal": ringkasan_response_data.estimasi_balik_modal,
                "kesimpulan_ringkasan": ringkasan_response_data.kesimpulan_ringkasan,
                "ai_analysis": {
                    "status": ai_analysis_info.status,
                    "model_used": ai_analysis_info.model_used,
                    "source": ai_analysis_info.source,
                    "message": ai_analysis_info.message
                }
            },
            "progress": 100
        }
        
        yield f"data: {json.dumps(final_response, ensure_ascii=False)}\n\n"
        
        logger.info(f"✅ Project created dengan streaming: {new_project.id}")
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {str(e)}")
        db.rollback()
        error_response = {
            "type": "error",
            "message": f"Error dalam analisis AI: {str(e)}",
            "progress": 0
        }
        yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"
    except Exception as e:
        logger.error(f"❌ Error creating project: {str(e)}")
        db.rollback()
        error_response = {
            "type": "error",
            "message": f"Gagal membuat project: {str(e)}",
            "progress": 0
        }
        yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"
