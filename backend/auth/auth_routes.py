"""FastAPI router for Authentication and User management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from backend.database.session import get_db
from backend.auth.hashing import Hasher
from backend.auth.jwt import create_access_token
from backend.auth.security import get_current_active_user
from backend.models.user import User
from backend.schemas.schemas import (
    UserCreate,
    UserLogin,
    UserUpdate,
    UserPasswordChange,
    UserResponse,
    TokenResponse
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    # Check if this is the first registered user, make them Admin
    user_count = db.query(User).count()
    role = "Admin" if user_count == 0 else "User"
    
    hashed_pwd = Hasher.get_password_hash(user_in.password)
    new_user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        password_hash=hashed_pwd,
        role=role,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate credentials and return JWT access token."""
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not Hasher.verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
        
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/logout")
async def logout():
    """Stateful logout feedback endpoint. Tokens are cleared on client side."""
    return {"detail": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Retrieve details of currently logged in user."""
    return current_user

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user's full name or email profile fields."""
    if profile_data.email != current_user.email:
        # Check if email is already taken
        email_taken = db.query(User).filter(User.email == profile_data.email).first()
        if email_taken:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
            
    current_user.full_name = profile_data.full_name
    current_user.email = profile_data.email
    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/change-password")
async def change_password(
    pwd_data: UserPasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Securely update currently authenticated user password."""
    if not Hasher.verify_password(pwd_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
        
    current_user.password_hash = Hasher.get_password_hash(pwd_data.new_password)
    db.commit()
    return {"detail": "Password updated successfully"}

@router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete currently authenticated user account and their ownership records."""
    db.delete(current_user)
    db.commit()
    return {"detail": "Account deleted successfully"}
