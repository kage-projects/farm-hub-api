from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from app.database import get_session
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate, ProjectUpdateResponse, ProjectDetailResponse, ProjectListResponse
from app.controllers.project_controller import create_project_with_analysis, update_project_partial, get_project_by_id, get_projects
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
    """Create project dengan streaming response dari AI analysis
    
    Response menggunakan Server-Sent Events (SSE) format.
    Client dapat menerima chunk-chunk response secara real-time.
    
    Format response:
    - data: {"type": "status", "message": "...", "progress": 10}
    - data: {"type": "chunk", "text": "...", "progress": 50}
    - data: {"type": "result", "data": {...}, "progress": 90}
    - data: {"type": "completed", "success": true, "data": {...}, "ringkasan_awal": {...}, "progress": 100}
    - data: {"type": "error", "message": "...", "progress": 0}
    """
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


