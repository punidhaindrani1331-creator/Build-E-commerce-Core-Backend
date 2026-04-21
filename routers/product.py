from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

import models, schemas
from database import get_db
import json
from redis_client import redis_client
import redis
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from auth import decode_access_token
from routers.cart import get_current_user_id

oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

def get_current_user_id_optional(token: Optional[str] = Depends(oauth2_scheme_optional)):
    if not token:
        return None
    payload = decode_access_token(token)
    return payload.get("user_id") if payload else None

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

# Public Product Endpoints (Accessible to all)
@router.get("/", response_model=List[schemas.Product])

def read_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of products with optional search and filtering. Accessible to all.
    """
    # Only cache raw list without filters to keep it simple, matching "products:list"
    is_simple_list = not search and not category and min_price is None and max_price is None and skip == 0 and limit == 100
    
    if is_simple_list:
        try:
            cached_products = redis_client.get("products:list")
            if cached_products:
                return json.loads(cached_products)
        except redis.exceptions.RedisError as e:
            print(f"Redis cache read failed: {e}")

    query = db.query(models.Product)
    
    if search:
        query = query.filter(models.Product.name.contains(search) | models.Product.description.contains(search))
    if category:
        query = query.filter(models.Product.category == category)
    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)
        
    products = query.offset(skip).limit(limit).all()
    
    if is_simple_list:
        try:
            redis_client.set("products:list", json.dumps(jsonable_encoder(products)), ex=3600)
        except redis.exceptions.RedisError as e:
            print(f"Redis cache write failed: {e}")
        
    return products

@router.get("/user/recent", response_model=List[schemas.Product])
def get_recently_viewed(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Return last 5 viewed products for the current user.
    """
    try:
        key = f"recent:user:{user_id}"
        product_ids_str = redis_client.lrange(key, 0, 4)
        if not product_ids_str:
            return []
            
        # Convert to list of ints
        product_ids = [int(pid) for pid in product_ids_str]
        
        # Fetch from DB and preserve the order
        products = db.query(models.Product).filter(models.Product.id.in_(product_ids)).all()
        product_map = {p.id: p for p in products}
        
        ordered_products = [product_map[pid] for pid in product_ids if pid in product_map]
        return ordered_products
    except redis.exceptions.RedisError as e:
        print(f"Redis recent products read failed: {e}")
        return []

@router.get("/{product_id}", response_model=schemas.Product)
def read_product(
    product_id: int, 
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(get_current_user_id_optional)
):
    """
    Retrieve a specific product by its ID. Accessible to all.
    Logs to recently viewed if a user is authenticated.
    """
    try:
        cached_product = redis_client.get(f"product:{product_id}")
        if cached_product:
            return json.loads(cached_product)
    except redis.exceptions.RedisError as e:
        print(f"Redis cache read failed: {e}")
        
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
        
    try:
        redis_client.set(f"product:{product_id}", json.dumps(jsonable_encoder(db_product)), ex=3600)
        
        # Store in recently viewed list if user is logged in
        if user_id:
            key = f"recent:user:{user_id}"
            redis_client.lrem(key, 0, product_id) # Remove existing to move it to the top
            redis_client.lpush(key, product_id)
            redis_client.ltrim(key, 0, 4) # Keep only last 5 elements
            
    except redis.exceptions.RedisError as e:
        print(f"Redis cache write/recent failed: {e}")
    return db_product
