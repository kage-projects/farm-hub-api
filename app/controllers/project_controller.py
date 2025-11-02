import logging
from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.project import Project
from app.models.ringkasan_awal import RingkasanAwal, PotensiPasar
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectData, RingkasanAwalData, RingkasanAwalDataSimple, AIAnalysisInfo, ProjectUpdate, ProjectUpdateResponse, ProjectDetailResponse, ProjectListResponse, ProjectListItem
from app.service.generative.prompt_ringkasan_awal import analyze_project_with_gemini

logger = logging.getLogger(__name__)

def create_project_with_analysis(
    db: Session,
    project_data: ProjectCreate,
    user_id: str
) -> ProjectResponse:

    try:
        # Generate project name jika tidak diisi
        project_name = project_data.project_name
        if not project_name:
            # Auto-generate project name jika tidak diisi
            project_name = f"Project {project_data.jenis_ikan.value} - {project_data.kabupaten_id}"
        
        logger.info(f"🔍 Memulai analisis project: {project_name}")
        analysis_result = analyze_project_with_gemini(
            project_name=project_name,
            jenis_ikan=project_data.jenis_ikan,
            modal=project_data.modal,
            kabupaten_id=project_data.kabupaten_id,
            resiko=project_data.resiko,
            lang=project_data.lang,
            lat=project_data.lat
        )
        
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
        
        
        new_ringkasan = RingkasanAwal(
            project_id=new_project.id,
            skor_kelayakan=analysis_result["skor_kelayakan"],
            potensi_pasar=PotensiPasar(analysis_result["potensi_pasar"]),
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
            modal=new_project.modal,
            kabupaten_id=new_project.kabupaten_id,
            resiko=get_enum_value(new_project.resiko),
            user_id=new_project.user_id,
            lang=new_project.lang,
            lat=new_project.lat
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

def update_project_partial(
    db: Session,
    project_id: str,
    update_data: ProjectUpdate,
    user_id: str
) -> ProjectUpdateResponse:
    """
    Update sebagian field project (PATCH) dan re-analyze dengan AI
    Hanya field yang diisi saja yang akan diupdate, kemudian ringkasan_awal akan di-regenerate
    """
    try:
        # 1. Cari project berdasarkan ID dan pastikan milik user
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project tidak ditemukan"
            )
        
        if project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak memiliki akses untuk mengupdate project ini"
            )
        
        # 2. Update field yang ada di update_data (hanya yang tidak None)
        updated_fields = []
        
        if update_data.project_name is not None:
            project.project_name = update_data.project_name
            updated_fields.append("project_name")
        
        if update_data.jenis_ikan is not None:
            # Pastikan enum di-convert dengan benar
            if isinstance(update_data.jenis_ikan, str):
                from app.models.project import JenisIkan
                project.jenis_ikan = JenisIkan(update_data.jenis_ikan)
            else:
                project.jenis_ikan = update_data.jenis_ikan
            updated_fields.append("jenis_ikan")
        
        if update_data.modal is not None:
            project.modal = update_data.modal
            updated_fields.append("modal")
        
        if update_data.kabupaten_id is not None:
            project.kabupaten_id = update_data.kabupaten_id
            updated_fields.append("kabupaten_id")
        
        if update_data.resiko is not None:
            # Pastikan enum di-convert dengan benar
            if isinstance(update_data.resiko, str):
                from app.models.project import Resiko
                project.resiko = Resiko(update_data.resiko)
            else:
                project.resiko = update_data.resiko
            updated_fields.append("resiko")
        
        if update_data.lang is not None:
            project.lang = update_data.lang
            updated_fields.append("lang")
        
        if update_data.lat is not None:
            project.lat = update_data.lat
            updated_fields.append("lat")
        
        # 3. Jika tidak ada field yang diupdate
        if not updated_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tidak ada field yang diupdate. Minimal satu field harus diisi."
            )
        
        # 4. Commit perubahan project terlebih dahulu
        db.add(project)
        db.commit()
        db.refresh(project)
        
        logger.info(f"✅ Project updated: {project.id}, Fields updated: {', '.join(updated_fields)}")
        
        # 5. Re-analyze project dengan Gemini AI karena ada perubahan
        logger.info(f"🔄 Re-analyzing project dengan data terbaru...")
        
        # Helper untuk memastikan enum di-convert ke object enum sebelum dikirim ke Gemini
        def ensure_enum(enum_obj, enum_class):
            """Convert string ke enum object jika perlu"""
            if enum_obj is None:
                return None
            if isinstance(enum_obj, str):
                return enum_class(enum_obj)
            if isinstance(enum_obj, enum_class):
                return enum_obj
            return enum_obj
        
        # Pastikan enum dalam format yang benar sebelum dikirim ke Gemini
        from app.models.project import JenisIkan, Resiko
        jenis_ikan_enum = ensure_enum(project.jenis_ikan, JenisIkan)
        resiko_enum = ensure_enum(project.resiko, Resiko)
        
        analysis_result = analyze_project_with_gemini(
            project_name=project.project_name,
            jenis_ikan=jenis_ikan_enum,
            modal=project.modal,
            kabupaten_id=project.kabupaten_id,
            resiko=resiko_enum,
            lang=project.lang,
            lat=project.lat
        )
        
        # 6. Update atau create ringkasan_awal dengan hasil analisis baru
        # Cari ringkasan_awal berdasarkan project_id (bukan primary key)
        existing_ringkasan = db.exec(
            select(RingkasanAwal).where(RingkasanAwal.project_id == project.id)
        ).first()
        
        if existing_ringkasan:
            # Update ringkasan_awal yang sudah ada
            existing_ringkasan.skor_kelayakan = analysis_result["skor_kelayakan"]
            existing_ringkasan.potensi_pasar = PotensiPasar(analysis_result["potensi_pasar"])
            existing_ringkasan.estimasi_balik_modal = analysis_result["estimasi_balik_modal"]
            existing_ringkasan.kesimpulan_ringkasan = analysis_result["kesimpulan_ringkasan"]
            db.add(existing_ringkasan)
            ringkasan = existing_ringkasan
            logger.info(f"✅ Ringkasan awal updated untuk project: {project.id}")
        else:
            # Create ringkasan_awal baru jika belum ada
            new_ringkasan = RingkasanAwal(
                project_id=project.id,
                skor_kelayakan=analysis_result["skor_kelayakan"],
                potensi_pasar=PotensiPasar(analysis_result["potensi_pasar"]),
                estimasi_balik_modal=analysis_result["estimasi_balik_modal"],
                kesimpulan_ringkasan=analysis_result["kesimpulan_ringkasan"]
            )
            db.add(new_ringkasan)
            ringkasan = new_ringkasan
            logger.info(f"✅ Ringkasan awal created untuk project: {project.id}")
        
        db.commit()
        db.refresh(ringkasan)
        
        # 7. Helper function untuk mendapatkan value dari enum atau string
        def get_enum_value(enum_obj):
            """Helper untuk mendapatkan value dari enum atau string"""
            if enum_obj is None:
                return None
            if isinstance(enum_obj, str):
                return enum_obj
            if hasattr(enum_obj, 'value'):
                return enum_obj.value
            return str(enum_obj)
        
        # Refresh project untuk memastikan data terbaru
        db.refresh(project)
        
        # 8. Prepare response
        project_response_data = ProjectData(
            id=project.id,
            project_name=project.project_name,
            jenis_ikan=get_enum_value(project.jenis_ikan),
            modal=project.modal,
            kabupaten_id=project.kabupaten_id,
            resiko=get_enum_value(project.resiko),
            user_id=project.user_id,
            lang=project.lang,
            lat=project.lat
        )
        
        # 9. Prepare AI Analysis Info
        ai_model_used = analysis_result.get("ai_model_used", "unknown")
        ai_success = analysis_result.get("ai_analysis_success", False)
        
        ai_analysis_info = AIAnalysisInfo(
            status="success" if ai_success else "failed",
            model_used=ai_model_used,
            source="gemini",
            message=f"Analisis berhasil dilakukan menggunakan {ai_model_used}" if ai_success else "Analisis AI gagal"
        )
        
        # Refresh ringkasan untuk memastikan data terbaru
        db.refresh(ringkasan)
        
        ringkasan_response_data = RingkasanAwalData(
            skor_kelayakan=ringkasan.skor_kelayakan,
            potensi_pasar=get_enum_value(ringkasan.potensi_pasar),
            estimasi_balik_modal=ringkasan.estimasi_balik_modal,
            kesimpulan_ringkasan=ringkasan.kesimpulan_ringkasan,
            ai_analysis=ai_analysis_info
        )
        
        return ProjectUpdateResponse(
            success=True,
            message=f"Project berhasil diupdate dan dianalisis ulang. Field yang diupdate: {', '.join(updated_fields)}",
            data=project_response_data,
            ringkasan_awal=ringkasan_response_data
        )
        
    except HTTPException:
        db.rollback()
        raise
    except ValueError as e:
        logger.error(f"❌ Validation error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error dalam analisis AI: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Error updating project: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengupdate project: {str(e)}"
        )

def get_project_by_id(
    db: Session,
    project_id: str,
    user_id: str
) -> ProjectDetailResponse:
    """
    Get project detail berdasarkan ID
    """
    try:
        # 1. Cari project berdasarkan ID dan pastikan milik user
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project tidak ditemukan"
            )
        
        if project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak memiliki akses untuk melihat project ini"
            )
        
        # 2. Cari ringkasan_awal berdasarkan project_id
        ringkasan = db.exec(
            select(RingkasanAwal).where(RingkasanAwal.project_id == project.id)
        ).first()
        
        if not ringkasan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ringkasan awal project tidak ditemukan"
            )
        
        # 3. Helper function untuk mendapatkan value dari enum atau string
        def get_enum_value(enum_obj):
            """Helper untuk mendapatkan value dari enum atau string"""
            if enum_obj is None:
                return None
            if isinstance(enum_obj, str):
                return enum_obj
            if hasattr(enum_obj, 'value'):
                return enum_obj.value
            return str(enum_obj)
        
        # 4. Prepare response
        project_response_data = ProjectData(
            id=project.id,
            project_name=project.project_name,
            jenis_ikan=get_enum_value(project.jenis_ikan),
            modal=project.modal,
            kabupaten_id=project.kabupaten_id,
            resiko=get_enum_value(project.resiko),
            user_id=project.user_id,
            lang=project.lang,
            lat=project.lat
        )
        
        ringkasan_response_data = RingkasanAwalDataSimple(
            ringkasanId=ringkasan.id,
            skor_kelayakan=ringkasan.skor_kelayakan,
            potensi_pasar=get_enum_value(ringkasan.potensi_pasar),
            estimasi_balik_modal=ringkasan.estimasi_balik_modal,
            kesimpulan_ringkasan=ringkasan.kesimpulan_ringkasan
        )
        
        return ProjectDetailResponse(
            success=True,
            message="Project berhasil ditemukan",
            data=project_response_data,
            ringkasan_awal=ringkasan_response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil project: {str(e)}"
        )

def get_projects(
    db: Session,
    user_id: str
) -> ProjectListResponse:
    """
    Get list semua project milik user
    """
    try:
        # 1. Query semua project milik user
        projects = db.exec(
            select(Project).where(Project.user_id == user_id)
        ).all()
        
        # 2. Helper function untuk mendapatkan value dari enum atau string
        def get_enum_value(enum_obj):
            """Helper untuk mendapatkan value dari enum atau string"""
            if enum_obj is None:
                return None
            if isinstance(enum_obj, str):
                return enum_obj
            if hasattr(enum_obj, 'value'):
                return enum_obj.value
            return str(enum_obj)
        
        # 3. Convert ke ProjectListItem
        project_list = [
            ProjectListItem(
                id=project.id,
                project_name=project.project_name,
                kabupaten_id=project.kabupaten_id,
                resiko=get_enum_value(project.resiko)
            )
            for project in projects
        ]
        
        return ProjectListResponse(
            success=True,
            message=f"Berhasil mengambil {len(project_list)} project",
            data=project_list
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting projects list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil list project: {str(e)}"
        )

