from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import (
    UserRegister, 
    UserLogin, 
    LoginResponse, 
    RegisterResponse,
    LoginData,
    RegisterData
)
from app.utils.security import get_password_hash, verify_password, create_access_token
from datetime import timedelta
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

def register_user(db: Session, user_data: UserRegister) -> RegisterResponse:
    """Register a new user - Mapping schema di controller"""
    try:
        statement = select(User).where(User.email == user_data.email)
        existing_user = db.exec(statement).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate password length before hashing (bcrypt limit: 72 bytes)
        if len(user_data.password.encode('utf-8')) > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password cannot be longer than 72 characters"
            )
        
        hashed_password = get_password_hash(user_data.password)
        
        user = User(
            name=user_data.nama, 
            email=user_data.email,
            password=hashed_password
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"User registered successfully: {user.email}")
        
        return RegisterResponse(
            success=True,
            message="success regis",
            data=RegisterData(
                id=user.id,
                nama=user.name, 
                email=user.email
            )
        )
    
    except HTTPException:
        raise
    
    except ValueError as e:
        # Handle password length validation errors
        db.rollback()
        if "72" in str(e).lower() or "password" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password cannot be longer than 72 characters"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering user: {str(e)}", exc_info=True)
        # Log full error untuk debugging
        error_detail = str(e)
        logger.error(f"Full error details: {error_detail}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user. Please try again later."
        )

def authenticate_user(db: Session, login_data: UserLogin) -> LoginResponse:
    """Authenticate user and return token - Mapping schema di controller"""
    try:
        statement = select(User).where(User.email == login_data.email)
        user = db.exec(statement).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not verify_password(login_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=access_token_expires
        )
        
        logger.info(f"User authenticated successfully: {user.email}")
        
        return LoginResponse(
            success=True,
            message="success login",
            data=LoginData(token=access_token)
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error authenticating user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate user. Please try again later."
        )