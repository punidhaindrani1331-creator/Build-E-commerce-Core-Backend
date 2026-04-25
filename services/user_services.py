from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import models

def validate_user_not_exists(db: Session, email: str, username: str):
    db_user = db.query(models.User).filter(
        (models.User.email == email) | (models.User.username == username)
    ).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already registered")
