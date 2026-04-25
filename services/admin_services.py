from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import models

def validate_admin_secret(secret: str, expected_secret: str):
    if secret != expected_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Admin Secret Key")
