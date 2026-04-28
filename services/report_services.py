from sqlalchemy.orm import Session
from sqlalchemy import func
import models
from redis_client import redis_client

def get_top_selling_products(db: Session, limit: int = 5):
    """
    Retrieves the top selling products based on total quantity sold.
    Calculates total revenue per product as well.
    """
    results = db.query(
        models.OrderItem.product_id,
        models.Product.name.label("product_name"),
        func.sum(models.OrderItem.quantity).label("total_quantity"),
        func.sum(models.OrderItem.quantity * models.OrderItem.price).label("total_revenue")
    ).join(
        models.Product, models.OrderItem.product_id == models.Product.id
    ).group_by(
        models.OrderItem.product_id, models.Product.name
    ).order_by(
        func.sum(models.OrderItem.quantity).desc()
    ).limit(limit).all()
    
    return results

def get_slow_apis(limit: int = 10):
    """
    Retrieves the slowest APIs from Redis sorted set.
    """
    try:
        # Get elements sorted by score (time) descending
        slow_apis = redis_client.zrevrange("reports:slow_apis", 0, limit - 1, withscores=True)
        return slow_apis
    except Exception as e:
        print(f"Redis get_slow_apis error: {e}")
        return []
