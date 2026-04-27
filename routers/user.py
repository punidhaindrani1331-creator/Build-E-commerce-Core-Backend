from fastapi import APIRouter, Depends, HTTPException, status
import os

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import models, schemas, auth
from services import user_services
from database import get_db

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register", response_model=schemas.StandardResponse[schemas.User], status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user with a hashed password.
    """
    # Check if user already exists
    user_services.validate_user_not_exists(db, user.email, user.username)

    # Create new user
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username.strip(),
        email=user.email.strip().lower(),
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "success": True,
        "message": "User registered successfully",
        "data": new_user
    }

@router.post("/login", response_model=schemas.StandardResponse[dict])
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT access token.
    Note: username field in OAuth2PasswordRequestForm is used for email in this case.
    """
    # Find user by email OR username (normalized)
    input_identifier = form_data.username.strip()
    db_user = db.query(models.User).filter(
        (models.User.email == input_identifier.lower()) | (models.User.username == input_identifier)
    ).first()
    
    if not db_user or not auth.verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token(data={"user_id": db_user.id})
    return {
        "success": True,
        "message": "Login successful",
        "data": {"access_token": access_token, "token_type": "bearer"}
    }
