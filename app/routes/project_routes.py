from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from app.database import get_session
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate, ProjectUpdateResponse
from app.controllers.project_controller import create_project_with_analysis, update_project_partial
from app.middleware.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter()

@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["projects"]
)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create project baru dengan analisis AI menggunakan Gemini
    
    - **project_name**: Nama project (opsional, akan auto-generate "Project 1", "Project 2", dst jika tidak diisi)
    - **jenis_ikan**: Jenis ikan (NILA, LELE, GURAME)
    - **jumlah_team**: Jumlah team (1 = solo, >1 = team)
    - **modal**: Modal dalam Rupiah
    - **kabupaten_id**: ID/Nama kabupaten di Sumatera Barat
    - **resiko**: Tingkat resiko (KONSERVATIF, MODERAT, AGRESIF)
    
    Response akan include analisis dari AI (ringkasan_awal)
    """
    return create_project_with_analysis(db, project_data, current_user.id)

@router.patch(
    "/projects/{project_id}",
    response_model=ProjectUpdateResponse,
    status_code=status.HTTP_200_OK,
    tags=["projects"]
)
def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update sebagian field project (PATCH) dengan re-analyze AI
    
    Setelah update, project akan dianalisis ulang menggunakan Gemini AI dan ringkasan_awal akan di-update.
    
    Field yang bisa diupdate (semua optional):
    - **project_name**: Nama project
    - **jenis_ikan**: Jenis ikan (NILA, LELE, GURAME)
    - **jumlah_team**: Jumlah team (1 = solo, >1 = team)
    - **modal**: Modal dalam Rupiah
    - **kabupaten_id**: ID/Nama kabupaten di Sumatera Barat
    - **resiko**: Tingkat resiko (KONSERVATIF, MODERAT, AGRESIF)
    
    **Contoh penggunaan:**
    - Update modal saja: `{"modal": 60000000}` - akan re-analyze dengan modal baru
    - Update modal dan jumlah team: `{"modal": 60000000, "jumlah_team": 2}` - akan re-analyze dengan data terbaru
    
    Response akan include ringkasan_awal yang sudah di-update dengan analisis baru.
    """
    return update_project_partial(db, project_id, update_data, current_user.id)


