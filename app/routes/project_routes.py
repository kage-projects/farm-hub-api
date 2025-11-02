from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from app.database import get_session
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate, ProjectUpdateResponse, ProjectDetailResponse, ProjectListResponse, AnalyzeResponse, RoadmapStepRequest, RoadmapStepUpdateResponse
from app.controllers.project_controller import create_project_with_analysis, update_project_partial, get_project_by_id, get_projects
from app.controllers.analyze_controller import analyze_project_data, get_analyze_data, update_roadmap_step
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
    """Create project dengan analisis AI (non-streaming)"""
    return create_project_with_analysis(db, project_data, current_user.id)

@router.post(
    "/projects/stream",
    status_code=status.HTTP_200_OK,
    tags=["projects"]
)
async def create_project_stream(
    project_data: ProjectCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    from app.controllers.project_controller_stream import create_project_with_streaming
    
    return StreamingResponse(
        create_project_with_streaming(db, project_data, current_user.id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
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

    return update_project_partial(db, project_id, update_data, current_user.id)

@router.get(
    "/projects",
    response_model=ProjectListResponse,
    status_code=status.HTTP_200_OK,
    tags=["projects"]
)
def list_projects(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get list semua project milik user yang sedang login
    """
    return get_projects(db, current_user.id)

@router.get(
    "/project/{project_id}",
    response_model=ProjectDetailResponse,
    status_code=status.HTTP_200_OK,
    tags=["projects"]
)
def get_project(
    project_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
 
    return get_project_by_id(db, project_id, current_user.id)

@router.post(
    "/analyze/{id_ringkasan}",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    tags=["projects"]
)
async def analyze(
    id_ringkasan: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Generate informasi teknis, analisis financial, dan roadmap menggunakan Gemini AI
    
    Menggunakan path parameter: POST /api/v1/analyze/{id_ringkasan}
    """
    return await analyze_project_data(db, id_ringkasan, current_user.id)

@router.get(
    "/analyze/{id_ringkasan}",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    tags=["projects"]
)
def get_analyze(
    id_ringkasan: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get informasi teknis, analisis financial, dan roadmap berdasarkan id_ringkasan
    
    Menggunakan path parameter: GET /api/v1/analyze/{id_ringkasan}
    """
    return get_analyze_data(db, id_ringkasan, current_user.id)

@router.patch(
    "/analyze/{id_ringkasan}/roadmap/step",
    response_model=RoadmapStepUpdateResponse,
    status_code=status.HTTP_200_OK,
    tags=["projects"]
)
async def patch_roadmap_step(
    id_ringkasan: str,
    step_request: RoadmapStepRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update roadmap dengan menambahkan sub-step untuk step tertentu berdasarkan request user
    
    User mengirim request/input dalam body dengan step number, kemudian AI akan generate title dan deskripsi sub-step.
    System otomatis menambahkan sub-step ke step yang ditentukan.
    Jika user mengirim request untuk step 1 pertama kali, akan menjadi sub-step 1.1
    Jika dilakukan lagi untuk step 1, akan menjadi 1.2, 1.3, dst.
    Jika user mengirim request untuk step 2, akan menjadi sub-step 2.1, 2.2, dst.
    
    Request body:
    - request (required): Input/masukkan dari user untuk sub-step
    - step (optional, default: 1): Nomor step utama (1-4) yang akan ditambahkan sub-stepnya
    
    Contoh:
    - PATCH /api/v1/analyze/{id_ringkasan}/roadmap/step dengan body {{"request": "bagaimana cara membersihkan kolam dengan baik", "step": 1}}
      → Menambahkan sub-step 1.1 dengan title dan deskripsi yang di-generate AI
    - PATCH /api/v1/analyze/{id_ringkasan}/roadmap/step lagi dengan body {{"request": "cara pasang terpal", "step": 1}}
      → Menambahkan sub-step 1.2
    - PATCH /api/v1/analyze/{id_ringkasan}/roadmap/step dengan body {{"request": "ikan saya mati semua", "step": 2}}
      → Menambahkan sub-step 2.1
    """
    return await update_roadmap_step(
        db, 
        id_ringkasan, 
        step_request.request,
        step_request.step,
        current_user.id
    )


