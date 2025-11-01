from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from app.database import get_session
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate, ProjectUpdateResponse, ProjectDetailResponse
from app.controllers.project_controller import create_project_with_analysis, update_project_partial, get_project_by_id
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

    return update_project_partial(db, project_id, update_data, current_user.id)

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


