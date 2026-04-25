from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os

import models, schemas, auth
from services import admin_services, user_services, product_services
from database import get_db
from routers.cart import get_current_admin
from redis_client import redis_client
import redis

router = APIRouter(
    prefix="/admin",
    tags=["Admin Operations"]
)

# Admin: Register (Protected by Secret Key, not JWT Admin status)
@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register_admin(user: schemas.AdminCreate, db: Session = Depends(get_db)):
    """
    Register a new ADMIN user. Requires a secret key from environment variables.
    """
    # Verify Admin Secret Key
    expected_secret = os.getenv("ADMIN_SECRET_KEY", "admin_secret_123")
    admin_services.validate_admin_secret(user.admin_secret, expected_secret)

    # Check if user already exists
    user_services.validate_user_not_exists(db, user.email.strip().lower(), user.username.strip())

    # Create new admin
    hashed_password = auth.get_password_hash(user.password)
    new_admin = models.User(
        username=user.username.strip(),
        email=user.email.strip().lower(),
        hashed_password=hashed_password,
        is_admin=1 # Set as admin
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin

# Admin: Add Product (Requires Admin JWT)
@router.post("/products", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def admin_add_product(
    product: schemas.ProductCreate, 
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """
    Create a new product in the store catalog. Restricted to Admin only.
    """
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Invalidate cache
    try:
        redis_client.delete("products:list")
    except redis.exceptions.RedisError as e:
        print(f"Redis cache delete failed: {e}")
    
    return db_product

# Admin: Update Stock (Requires Admin JWT)
@router.patch("/products/{product_id}/stock", response_model=schemas.Product)
def admin_update_stock(
    product_id: int, 
    stock_update: int, 
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """
    Update stock levels for a specific product. Restricted to Admin only.
    """
    db_product = product_services.validate_product_exists(db, product_id)
    
    db_product.stock = stock_update
    db.commit()
    db.refresh(db_product)
    
    # Invalidate cache
    try:
        redis_client.delete("products:list")
        redis_client.delete(f"product:{product_id}")
    except redis.exceptions.RedisError as e:
        print(f"Redis cache delete failed: {e}")
    
    return db_product

# Admin: Update Product (Requires Admin JWT)
@router.put("/products/{product_id}", response_model=schemas.Product)
def admin_update_product(
    product_id: int, 
    product_update: schemas.ProductUpdate, 
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """
    Update a product. Restricted to Admin only.
    """
    db_product = product_services.validate_product_exists(db, product_id)
    
    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
        
    db.commit()
    db.refresh(db_product)
    
    # Invalidate cache
    try:
        redis_client.delete("products:list")
        redis_client.delete(f"product:{product_id}")
    except redis.exceptions.RedisError as e:
        print(f"Redis cache delete failed: {e}")
    
    return db_product

# Admin: Delete Product (Requires Admin JWT)
@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_product(
    product_id: int, 
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """
    Delete a product. Restricted to Admin only.
    """
    db_product = product_services.validate_product_exists(db, product_id)
        
    db.delete(db_product)
    db.commit()
    
    # Invalidate cache
    try:
        redis_client.delete("products:list")
        redis_client.delete(f"product:{product_id}")
    except redis.exceptions.RedisError as e:
        print(f"Redis cache delete failed: {e}")
    
    return None

# Admin: View All Orders (Requires Admin JWT)
@router.get("/orders", response_model=List[schemas.OrderResponse])
def admin_view_all_orders(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """
    Retrieve all orders placed in the store. Restricted to Admin only.
    """
    orders = db.query(models.Order).all()
    return orders
