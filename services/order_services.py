from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import models

def validate_cart_not_empty(cart_items: list):
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

def validate_stock_sufficient(product: models.Product, requested_quantity: int):
    if product.stock < requested_quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"Not enough stock for product '{product.name}'. Available: {product.stock}"
        )

def validate_order_exists(order: models.Order):
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

def validate_order_ownership(order: models.Order, user_id: int):
    if order.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this order"
        )

def validate_order_cancellable(order: models.Order):
    if order.status != "placed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be cancelled. Current status: {order.status}"
        )
