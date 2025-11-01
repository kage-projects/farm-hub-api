from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from app.database import get_session
from app.schemas.project import ProjectCreate, ProjectResponse
from app.controllers.project_controller import create_project_with_analysis
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
    
    - **project_name**: Nama project
    - **jenis_ikan**: Jenis ikan (NILA, LELE, GURAME)
    - **jumlah_team**: Jumlah team (1 = solo, >1 = team)
    - **modal**: Modal dalam Rupiah
    - **kabupaten_id**: ID/Nama kabupaten di Sumatera Barat
    - **resiko**: Tingkat resiko (KONSERVATIF, MODERAT, AGRESIF)
    
    Response akan include analisis dari AI (ringkasan_awal)
    """
    return create_project_with_analysis(db, project_data, current_user.id)

