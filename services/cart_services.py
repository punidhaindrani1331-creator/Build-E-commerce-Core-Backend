from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import models

def validate_positive_quantity(quantity: int):
    if quantity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be greater than zero")

def validate_cart_item_exists(db: Session, cart_item_id: int, user_id: int):
    db_cart_item = db.query(models.CartItem).filter(
        models.CartItem.id == cart_item_id,
        models.CartItem.user_id == user_id
    ).first()
    if not db_cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    return db_cart_item
