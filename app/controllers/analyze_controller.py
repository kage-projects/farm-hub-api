import logging
import asyncio
import copy
from concurrent.futures import ThreadPoolExecutor
from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.project import Project
from app.models.ringkasan_awal import RingkasanAwal
from app.models.informasi_teknis import InformasiTeknis
from app.models.analisis_financial import AnalisisFinancial
from app.models.roadmap import Roadmap
from app.service.generative.prompt_informasi_teknis import generate_informasi_teknis_with_gemini
from app.service.generative.prompt_analisis_financial import generate_analisis_financial_with_gemini
from app.service.generative.prompt_roadmap import generate_roadmap_with_gemini
from app.service.generative.prompt_roadmap.substep_generator import SubStepGenerator

logger = logging.getLogger(__name__)

# Thread pool untuk menjalankan synchronous Gemini calls secara parallel
executor = ThreadPoolExecutor(max_workers=3)

def get_enum_value(enum_obj):
    """Helper untuk mendapatkan value dari enum atau string"""
    if enum_obj is None:
        return None
    if isinstance(enum_obj, str):
        return enum_obj
    if hasattr(enum_obj, 'value'):
        return enum_obj.value
    return str(enum_obj)

async def analyze_project_data(
    db: Session,
    id_ringkasan: str,
    user_id: str
) -> dict:
    """
    Generate informasi teknis, analisis financial, dan roadmap secara parallel
    """
    try:
        # 1. Cari ringkasan_awal berdasarkan ID
        ringkasan_awal = db.get(RingkasanAwal, id_ringkasan)
        if not ringkasan_awal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ringkasan awal tidak ditemukan"
            )
        
        # 2. Cari project berdasarkan project_id dari ringkasan_awal
        project = db.get(Project, ringkasan_awal.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project tidak ditemukan"
            )
        
        # 3. Verifikasi project milik user
        if project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak memiliki akses untuk menganalisis project ini"
            )
        
        # 4. Prepare data untuk prompt
        jenis_ikan_str = get_enum_value(project.jenis_ikan)
        resiko_str = get_enum_value(project.resiko)
        potensi_pasar_str = get_enum_value(ringkasan_awal.potensi_pasar)
        
        # 5. Generate informasi_teknis terlebih dahulu (karena diperlukan untuk analisis_financial dan roadmap)
        logger.info(f"🔍 Memulai generate informasi teknis untuk project: {project.project_name}")
        
        informasi_teknis_result = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: generate_informasi_teknis_with_gemini(
                project_name=project.project_name,
                jenis_ikan=jenis_ikan_str,
                modal=project.modal,
                kabupaten_id=project.kabupaten_id,
                resiko=resiko_str,
                skor_kelayakan=ringkasan_awal.skor_kelayakan,
                potensi_pasar=potensi_pasar_str,
                estimasi_balik_modal=ringkasan_awal.estimasi_balik_modal,
                kesimpulan_ringkasan=ringkasan_awal.kesimpulan_ringkasan,
                lang=project.lang,
                lat=project.lat
            )
        )
        
        logger.info(f"✅ Informasi teknis berhasil di-generate")
        
        # 6. Generate analisis_financial terlebih dahulu (karena diperlukan untuk roadmap)
        logger.info(f"🔍 Memulai generate analisis financial")
        
        analisis_financial_result = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: generate_analisis_financial_with_gemini(
                project_name=project.project_name,
                jenis_ikan=jenis_ikan_str,
                modal=project.modal,
                kabupaten_id=project.kabupaten_id,
                resiko=resiko_str,
                skor_kelayakan=ringkasan_awal.skor_kelayakan,
                potensi_pasar=potensi_pasar_str,
                estimasi_balik_modal=ringkasan_awal.estimasi_balik_modal,
                kesimpulan_ringkasan=ringkasan_awal.kesimpulan_ringkasan,
                informasi_teknis=informasi_teknis_result,
                lang=project.lang,
                lat=project.lat
            )
        )
        
        logger.info(f"✅ Analisis financial berhasil di-generate")
        
        # 7. Generate roadmap dengan informasi_teknis dan analisis_financial yang lengkap
        logger.info(f"🔍 Memulai generate roadmap")
        
        roadmap_result = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: generate_roadmap_with_gemini(
                project_name=project.project_name,
                jenis_ikan=jenis_ikan_str,
                modal=project.modal,
                kabupaten_id=project.kabupaten_id,
                resiko=resiko_str,
                skor_kelayakan=ringkasan_awal.skor_kelayakan,
                potensi_pasar=potensi_pasar_str,
                estimasi_balik_modal=ringkasan_awal.estimasi_balik_modal,
                kesimpulan_ringkasan=ringkasan_awal.kesimpulan_ringkasan,
                informasi_teknis=informasi_teknis_result,
                analisis_financial=analisis_financial_result,
                lang=project.lang,
                lat=project.lat
            )
        )
        
        logger.info(f"✅ Roadmap berhasil di-generate")
        
        # 8. Save ke database
        # Cek apakah sudah ada informasi_teknis
        existing_informasi_teknis = db.exec(
            select(InformasiTeknis).where(InformasiTeknis.project_id == project.id)
        ).first()
        
        if existing_informasi_teknis:
            existing_informasi_teknis.spesifikasi_kolam = informasi_teknis_result.get("spesifikasiKolam")
            existing_informasi_teknis.kualitas_air = informasi_teknis_result.get("kualitasAir")
            existing_informasi_teknis.spesifikasi_benih = informasi_teknis_result.get("spesifikasiBenih")
            existing_informasi_teknis.spesifikasi_pakan = informasi_teknis_result.get("spesifikasiPakan")
            existing_informasi_teknis.manajemen_kesehatan = informasi_teknis_result.get("manajemenKesehatan")
            existing_informasi_teknis.teknologi_pendukung = informasi_teknis_result.get("teknologiPendukung")
            db.add(existing_informasi_teknis)
            logger.info(f"✅ Informasi teknis updated untuk project: {project.id}")
        else:
            new_informasi_teknis = InformasiTeknis(
                project_id=project.id,
                spesifikasi_kolam=informasi_teknis_result.get("spesifikasiKolam"),
                kualitas_air=informasi_teknis_result.get("kualitasAir"),
                spesifikasi_benih=informasi_teknis_result.get("spesifikasiBenih"),
                spesifikasi_pakan=informasi_teknis_result.get("spesifikasiPakan"),
                manajemen_kesehatan=informasi_teknis_result.get("manajemenKesehatan"),
                teknologi_pendukung=informasi_teknis_result.get("teknologiPendukung")
            )
            db.add(new_informasi_teknis)
            logger.info(f"✅ Informasi teknis created untuk project: {project.id}")
        
        # Cek apakah sudah ada analisis_financial
        existing_analisis_financial = db.exec(
            select(AnalisisFinancial).where(AnalisisFinancial.project_id == project.id)
        ).first()
        
        if existing_analisis_financial:
            existing_analisis_financial.rincian_modal_awal = analisis_financial_result.get("rincianModalAwal")
            existing_analisis_financial.biaya_operasional = analisis_financial_result.get("biayaOperasional")
            existing_analisis_financial.analisis_roi = analisis_financial_result.get("analisisROI")
            existing_analisis_financial.analisis_bep = analisis_financial_result.get("analisisBEP")
            existing_analisis_financial.proyeksi_pendapatan = analisis_financial_result.get("proyeksiPendapatan")
            db.add(existing_analisis_financial)
            logger.info(f"✅ Analisis financial updated untuk project: {project.id}")
        else:
            new_analisis_financial = AnalisisFinancial(
                project_id=project.id,
                rincian_modal_awal=analisis_financial_result.get("rincianModalAwal"),
                biaya_operasional=analisis_financial_result.get("biayaOperasional"),
                analisis_roi=analisis_financial_result.get("analisisROI"),
                analisis_bep=analisis_financial_result.get("analisisBEP"),
                proyeksi_pendapatan=analisis_financial_result.get("proyeksiPendapatan")
            )
            db.add(new_analisis_financial)
            logger.info(f"✅ Analisis financial created untuk project: {project.id}")
        
        # Hapus roadmap lama jika ada (karena roadmap hanya 1 data row per project)
        existing_roadmaps = db.exec(
            select(Roadmap).where(Roadmap.project_id == project.id)
        ).all()
        
        for roadmap in existing_roadmaps:
            db.delete(roadmap)
        
        # Create roadmap baru
        # Pastikan step adalah float
        roadmap_step = roadmap_result.get("step", 1.0)
        if not isinstance(roadmap_step, (int, float)):
            roadmap_step = 1.0
        else:
            roadmap_step = float(roadmap_step)
        
        new_roadmap = Roadmap(
            project_id=project.id,
            response=roadmap_result.get("response"),
            request=roadmap_result.get("request"),
            step=roadmap_step,
            is_request=roadmap_result.get("isRequest", False),
            roadmap_id=roadmap_result.get("roadmapId")
        )
        db.add(new_roadmap)
        logger.info(f"✅ Roadmap created untuk project: {project.id}")
        
        # Commit semua perubahan
        db.commit()
        
        # 9. Prepare response
        response_data = {
            "informasi_teknis": informasi_teknis_result,
            "analisis_financial": analisis_financial_result,
            "roadmap": roadmap_result
        }
        
        logger.info(f"✅ Semua data berhasil di-generate dan disimpan untuk project: {project.id}")
        
        return {
            "success": True,
            "message": "data received",
            "data": response_data
        }
        
    except HTTPException:
        db.rollback()
        raise
    except ValueError as e:
        logger.error(f"❌ Validation error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error validasi data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Error saat generate data: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal generate data: {str(e)}"
        )

def get_analyze_data(
    db: Session,
    id_ringkasan: str,
    user_id: str
) -> dict:
    """
    Get informasi teknis, analisis financial, dan roadmap berdasarkan id_ringkasan
    """
    try:
        # 1. Cari ringkasan_awal berdasarkan ID
        ringkasan_awal = db.get(RingkasanAwal, id_ringkasan)
        if not ringkasan_awal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ringkasan awal tidak ditemukan"
            )
        
        # 2. Cari project berdasarkan project_id dari ringkasan_awal
        project = db.get(Project, ringkasan_awal.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project tidak ditemukan"
            )
        
        # 3. Verifikasi project milik user
        if project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak memiliki akses untuk melihat data project ini"
            )
        
        # 4. Ambil informasi_teknis
        informasi_teknis = db.exec(
            select(InformasiTeknis).where(InformasiTeknis.project_id == project.id)
        ).first()
        
        informasi_teknis_data = None
        if informasi_teknis:
            # Convert dari snake_case (database) ke camelCase (response)
            informasi_teknis_data = {
                "spesifikasiKolam": informasi_teknis.spesifikasi_kolam,
                "kualitasAir": informasi_teknis.kualitas_air,
                "spesifikasiBenih": informasi_teknis.spesifikasi_benih,
                "spesifikasiPakan": informasi_teknis.spesifikasi_pakan,
                "manajemenKesehatan": informasi_teknis.manajemen_kesehatan,
                "teknologiPendukung": informasi_teknis.teknologi_pendukung
            }
        
        # 5. Ambil analisis_financial
        analisis_financial = db.exec(
            select(AnalisisFinancial).where(AnalisisFinancial.project_id == project.id)
        ).first()
        
        analisis_financial_data = None
        if analisis_financial:
            # Convert dari snake_case (database) ke camelCase (response)
            analisis_financial_data = {
                "rincianModalAwal": analisis_financial.rincian_modal_awal,
                "biayaOperasional": analisis_financial.biaya_operasional,
                "analisisROI": analisis_financial.analisis_roi,
                "analisisBEP": analisis_financial.analisis_bep,
                "proyeksiPendapatan": analisis_financial.proyeksi_pendapatan
            }
        
        # 6. Ambil roadmap (hanya yang pertama jika ada banyak)
        roadmap = db.exec(
            select(Roadmap).where(Roadmap.project_id == project.id)
        ).first()
        
        roadmap_data = None
        if roadmap:
            # Convert dari snake_case (database) ke camelCase (response)
            roadmap_data = {
                "response": roadmap.response,
                "request": roadmap.request,
                "step": roadmap.step,
                "isRequest": roadmap.is_request,
                "roadmapId": roadmap.roadmap_id
            }
        
        # 7. Prepare response
        response_data = {}
        
        if informasi_teknis_data:
            response_data["informasi_teknis"] = informasi_teknis_data
        else:
            response_data["informasi_teknis"] = None
        
        if analisis_financial_data:
            response_data["analisis_financial"] = analisis_financial_data
        else:
            response_data["analisis_financial"] = None
        
        if roadmap_data:
            response_data["roadmap"] = roadmap_data
        else:
            response_data["roadmap"] = None
        
        logger.info(f"✅ Data berhasil diambil untuk project: {project.id}")
        
        return {
            "success": True,
            "message": "data retrieved",
            "data": response_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error saat mengambil data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil data: {str(e)}"
        )

async def update_roadmap_step(
    db: Session,
    id_ringkasan: str,
    user_request: str,
    user_id: str
) -> dict:
    """
    Update roadmap dengan menambahkan sub-step untuk step pertama (step 1) berdasarkan request user
    
    Args:
        id_ringkasan: ID ringkasan awal
        user_request: Request/input dari user untuk sub-step baru
        user_id: ID user yang melakukan update
    
    System otomatis menambahkan sub-step ke step 1 (1.1, 1.2, 1.3, dst)
    """
    try:
        # 1. Cari ringkasan_awal berdasarkan ID
        ringkasan_awal = db.get(RingkasanAwal, id_ringkasan)
        if not ringkasan_awal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ringkasan awal tidak ditemukan"
            )
        
        # 2. Cari project berdasarkan project_id dari ringkasan_awal
        project = db.get(Project, ringkasan_awal.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project tidak ditemukan"
            )
        
        # 3. Verifikasi project milik user
        if project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak memiliki akses untuk mengupdate roadmap project ini"
            )
        
        # 4. Ambil roadmap
        roadmap = db.exec(
            select(Roadmap).where(Roadmap.project_id == project.id)
        ).first()
        
        if not roadmap or not roadmap.response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Roadmap tidak ditemukan. Silakan generate roadmap terlebih dahulu."
            )
        
        # 5. Otomatis menggunakan step 1 sebagai parent step
        parent_step_num = 1.0
        
        # 6. Dapatkan list steps dari response - COPY untuk menghindari mutating langsung
        roadmap_response = roadmap.response
        if not isinstance(roadmap_response, dict) or "list" not in roadmap_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format roadmap response tidak valid"
            )
        
        # Buat copy dari roadmap_response untuk memastikan tidak ada side effect
        roadmap_response_copy = copy.deepcopy(roadmap_response)
        steps_list = roadmap_response_copy.get("list", [])
        
        # Log untuk debugging - cek jumlah step sebelum update
        logger.info(f"📋 Step sebelum update: {len(steps_list)} step(s)")
        for step in steps_list:
            logger.debug(f"  - Step {step.get('step')}: {step.get('title', '')}")
        
        # 7. Cari step parent dan semua child step
        parent_step = None
        child_steps = []
        parent_step_index = None
        
        for idx, step in enumerate(steps_list):
            step_num = float(step.get("step", 0))
            # Step parent adalah yang step number-nya sama dengan step_number (tanpa decimal)
            if step_num == parent_step_num:
                parent_step = step
                parent_step_index = idx
            # Child step adalah yang step number-nya dimulai dengan parent_step_num (misal 1.1, 1.2 jika parent adalah 1)
            elif step_num > parent_step_num and step_num < parent_step_num + 1:
                child_steps.append((idx, step, step_num))
        
        if not parent_step:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Step {int(parent_step_num)} tidak ditemukan dalam roadmap"
            )
        
        # 8. Hitung nomor sub-step berikutnya
        # Jika sudah ada child steps, ambil yang terbesar dan tambah 0.1
        if child_steps:
            # Sort berdasarkan step number
            child_steps.sort(key=lambda x: x[2])
            last_child_num = child_steps[-1][2]
            # Hitung sub-step berikutnya
            new_sub_step_num = round(last_child_num + 0.1, 1)
            logger.info(f"📝 Sub-step terakhir: {last_child_num}, sub-step baru: {new_sub_step_num}")
        else:
            # Belum ada child step, mulai dari parent_step_num + 0.1
            new_sub_step_num = round(parent_step_num + 0.1, 1)
            logger.info(f"📝 Belum ada sub-step, membuat sub-step pertama: {new_sub_step_num}")
        
        # 9. Generate title dan deskripsi dari user request menggunakan Gemini AI
        logger.info(f"🔍 Generate sub-step {new_sub_step_num} dari user request untuk step {int(parent_step_num)}")
        
        # Ambil informasi_teknis untuk context
        informasi_teknis = db.exec(
            select(InformasiTeknis).where(InformasiTeknis.project_id == project.id)
        ).first()
        
        informasi_teknis_dict = None
        if informasi_teknis:
            informasi_teknis_dict = {
                "spesifikasiKolam": informasi_teknis.spesifikasi_kolam,
                "kualitasAir": informasi_teknis.kualitas_air,
                "spesifikasiBenih": informasi_teknis.spesifikasi_benih,
                "spesifikasiPakan": informasi_teknis.spesifikasi_pakan,
                "manajemenKesehatan": informasi_teknis.manajemen_kesehatan,
                "teknologiPendukung": informasi_teknis.teknologi_pendukung
            }
        
        jenis_ikan_str = get_enum_value(project.jenis_ikan)
        
        # Generate sub-step menggunakan Gemini
        substep_generator = SubStepGenerator()
        substep_content = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: substep_generator.generate_substep_from_request(
                user_request=user_request,
                parent_step_title=parent_step.get("title", ""),
                parent_step_deskripsi=parent_step.get("deskripsi", ""),
                project_name=project.project_name,
                jenis_ikan=jenis_ikan_str,
                informasi_teknis=informasi_teknis_dict
            )
        )
        
        logger.info(f"✅ Sub-step content berhasil di-generate")
        
        # 10. Buat sub-step baru
        new_sub_step = {
            "step": new_sub_step_num,
            "title": substep_content["title"],
            "deskripsi": substep_content["deskripsi"]
        }
        
        # 11. Insert sub-step setelah parent step atau setelah child step terakhir
        if child_steps:
            # Insert setelah child step terakhir
            insert_index = child_steps[-1][0] + 1
        else:
            # Insert setelah parent step
            insert_index = parent_step_index + 1
        
        # Pastikan insert index valid
        if insert_index > len(steps_list):
            insert_index = len(steps_list)
        
        # Insert sub-step baru - pastikan tidak menghapus step yang ada
        steps_list.insert(insert_index, new_sub_step)
        
        # Log untuk debugging - cek jumlah step setelah insert
        logger.info(f"📋 Step setelah insert: {len(steps_list)} step(s)")
        for step in steps_list:
            logger.debug(f"  - Step {step.get('step')}: {step.get('title', '')}")
        
        # 12. Update roadmap response dengan data yang sudah di-copy dan di-update
        roadmap_response_copy["list"] = steps_list
        roadmap.response = roadmap_response_copy  # Assign kembali ke roadmap
        roadmap.request = user_request  # Simpan request user terakhir
        
        # 13. Save ke database
        db.add(roadmap)
        db.commit()
        db.refresh(roadmap)
        
        logger.info(f"✅ Sub-step {new_sub_step_num} berhasil ditambahkan ke step {int(parent_step_num)} untuk project: {project.id}")
        
        # 14. Prepare response
        roadmap_data = {
            "response": roadmap.response,
            "request": roadmap.request,
            "step": roadmap.step,
            "isRequest": roadmap.is_request,
            "roadmapId": roadmap.roadmap_id
        }
        
        return {
            "success": True,
            "message": f"Sub-step {new_sub_step_num} berhasil ditambahkan ke step {int(parent_step_num)}",
            "data": {
                "roadmap": roadmap_data,
                "addedStep": new_sub_step
            }
        }
        
    except HTTPException:
        db.rollback()
        raise
    except ValueError as e:
        logger.error(f"❌ Validation error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error validasi data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Error saat update roadmap step: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal update roadmap step: {str(e)}"
        )

