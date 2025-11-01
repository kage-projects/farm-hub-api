from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from app.database import get_session
from app.schemas.auth import UserRegister, UserLogin, LoginResponse, RegisterResponse
from app.controllers.user_controller import register_user, authenticate_user

router = APIRouter()

@router.post("/registrasi", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def registrasi(user_data: UserRegister, db: Session = Depends(get_session)):
    return register_user(db, user_data) 

@router.post("/login", response_model=LoginResponse)
def login(credentials: UserLogin, db: Session = Depends(get_session)):
    return authenticate_user(db, credentials)  