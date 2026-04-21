from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List

import models, schemas, auth
from database import get_db

router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Real Authentication Dependency
def get_current_user_id(token: str = Depends(oauth2_scheme)):
    """
    Decodes the JWT token to extract the user_id.
    """
    payload = auth.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload.get("user_id")

# Admin Security Dependency
def get_current_admin(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Checks if the authenticated user has admin privileges.
    Returns 403 if not an admin.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.is_admin != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have administrative privileges"
        )
    return user

@router.post("/", response_model=schemas.CartItem)
def add_to_cart(
    item: schemas.CartItemCreate, 
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Add a product to the cart.
    - 400 if quantity is zero or negative.
    - 404 if product not found.
    """
    # 400 ERROR: Invalid quantity
    if item.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")

    # 404 ERROR: Product not found
    product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check if item already in cart for THIS specific user
    db_cart_item = db.query(models.CartItem).filter(
        models.CartItem.user_id == user_id,
        models.CartItem.product_id == item.product_id
    ).first()

    if db_cart_item:
        # Update quantity
        db_cart_item.quantity += item.quantity
    else:
        # Create new cart item
        db_cart_item = models.CartItem(
            user_id=user_id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(db_cart_item)

    db.commit()
    db.refresh(db_cart_item)
    return db_cart_item

@router.get("/", response_model=schemas.Cart)
def view_cart(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get all items in the current user's cart. Only shows OWN cart.
    """
    items = db.query(models.CartItem).filter(models.CartItem.user_id == user_id).all()
    
    total_price = sum(item.product.price * item.quantity for item in items)
    
    return {"items": items, "total_price": total_price}

@router.delete("/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    cart_item_id: int, 
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Remove an item from the cart. Ownership check enforced.
    """
    db_cart_item = db.query(models.CartItem).filter(
        models.CartItem.id == cart_item_id,
        models.CartItem.user_id == user_id
    ).first()

    if not db_cart_item:
        # Will fail if item doesn't exist OR belongs to another user
        raise HTTPException(status_code=404, detail="Cart item not found")

    db.delete(db_cart_item)
    db.commit()
    return None
