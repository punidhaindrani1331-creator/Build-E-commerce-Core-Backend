from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import models
import time
from typing import Optional, List, Tuple

def validate_product_exists(db: Session, product_id: int):
    start_time = time.time()
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    end_time = time.time()
    print(f"DEBUG: Product fetch took {end_time - start_time:.4f} sec")
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

def get_products(
    db: Session,
    search: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    offset: int = 0,
    limit: int = 10,
    sort_by: Optional[str] = None,
    order: str = "asc"
) -> Tuple[List[models.Product], int]:
    start_time = time.time()
    query = db.query(models.Product)

    if search:
        query = query.filter(models.Product.name.contains(search) | models.Product.description.contains(search))
    if category:
        query = query.filter(models.Product.category == category)
    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)

    # Get total count BEFORE applying offset/limit
    total_count = query.count()

    # Sorting with Whitelist
    allowed_sort_fields = ["price", "created_at", "name"]
    if sort_by in allowed_sort_fields:
        column = getattr(models.Product, sort_by)
        if order.lower() == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    products = query.offset(offset).limit(limit).all()
    end_time = time.time()
    print(f"DEBUG: Products list query took {end_time - start_time:.4f} sec")
    
    return products, total_count
