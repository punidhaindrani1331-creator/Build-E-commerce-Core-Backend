from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import models
import time

def validate_user_not_exists(db: Session, email: str, username: str):
    start_time = time.time()
    db_user = db.query(models.User).filter(
        (models.User.email == email) | (models.User.username == username)
    ).first()
    end_time = time.time()
    print(f"DEBUG: User exists check took {end_time - start_time:.4f} sec")
    
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already registered")
