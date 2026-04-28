from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional

import models, schemas
from services import product_services
from database import get_db
import json
from redis_client import redis_client
import redis
from fastapi.encoders import jsonable_encoder

from auth import get_current_user_id

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

# Public Product Endpoints (Accessible to all)

@router.get("/", response_model=schemas.StandardResponse[List[schemas.ProductSummary]])
def read_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    page: int = 1,
    limit: int = 10,
    sort_by: Optional[str] = None,
    order: str = "asc",
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Retrieve a list of products with optional search, filtering, sorting, and pagination. Accessible to all.
    Pagination: /products?page=1&limit=10
    Sorting: /products?sort_by=price&order=desc
    """
    # Rate Limiting Logic moved to service
    if request:
        product_services.validate_rate_limit(request.client.host, "products")

    # Pagination validation moved to service
    page, limit, offset = product_services.validate_pagination(page, limit)

    # Only cache raw list without filters/sorting to keep it simple, matching "products:list"
    is_simple_list = not search and not category and min_price is None and max_price is None and page == 1 and limit == 10 and not sort_by

    if is_simple_list:
        try:
            cached_data = redis_client.get("products:list")
            if cached_data:
                cached_json = json.loads(cached_data)
                return {
                    "success": True,
                    "message": "Data fetched successfully from cache",
                    "data": cached_json["products"],
                    "meta": {
                        "page": page,
                        "limit": limit,
                        "total": cached_json["total"]
                    }
                }
        except redis.exceptions.RedisError as e:
            print(f"Redis cache read failed: {e}")

    products, total_count = product_services.get_products(
        db=db,
        search=search,
        category=category,
        min_price=min_price,
        max_price=max_price,
        offset=offset,
        limit=limit,
        sort_by=sort_by,
        order=order
    )

    if is_simple_list:
        try:
            cache_payload = {
                "products": jsonable_encoder(products),
                "total": total_count
            }
            redis_client.set("products:list", json.dumps(cache_payload), ex=3600)
        except redis.exceptions.RedisError as e:
            print(f"Redis cache write failed: {e}")

    return {
        "success": True,
        "message": "Data fetched successfully",
        "data": products,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total_count
        }
    }

@router.get("/user/recent", response_model=schemas.StandardResponse[List[schemas.ProductSummary]])
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
            return {
                "success": True,
                "message": "No recently viewed products",
                "data": [],
                "meta": {"total": 0}
            }
            
        # Convert to list of ints
        product_ids = [int(pid) for pid in product_ids_str]
        
        # Fetch from DB and preserve the order
        products = db.query(models.Product).filter(models.Product.id.in_(product_ids)).all()
        product_map = {p.id: p for p in products}
        
        ordered_products = [product_map[pid] for pid in product_ids if pid in product_map]
        return {
            "success": True,
            "message": "Recently viewed products fetched",
            "data": ordered_products,
            "meta": {"total": len(ordered_products)}
        }
    except redis.exceptions.RedisError as e:
        print(f"Redis recent products read failed: {e}")
        return {
            "success": False,
            "message": "Could not fetch recently viewed products",
            "data": []
        }

@router.get("/{product_id}", response_model=schemas.StandardResponse[schemas.Product])
def read_product(
    product_id: int, 
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific product by its ID. Accessible to all.
    Logs to recently viewed if a user is authenticated.
    """
    try:
        cached_product = redis_client.get(f"product:{product_id}")
        if cached_product:
            return {
                "success": True,
                "message": "Product fetched from cache",
                "data": json.loads(cached_product)
            }
    except redis.exceptions.RedisError as e:
        print(f"Redis cache read failed: {e}")
        
    db_product = product_services.validate_product_exists(db, product_id)
        
    try:
        redis_client.set(f"product:{product_id}", json.dumps(jsonable_encoder(db_product)), ex=3600)
            
    except redis.exceptions.RedisError as e:
        print(f"Redis cache write failed: {e}")
        
    return {
        "success": True,
        "message": "Product fetched successfully",
        "data": db_product
    }
