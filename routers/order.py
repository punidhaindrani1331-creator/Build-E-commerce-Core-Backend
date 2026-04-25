from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
import time
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from services import order_services
from database import get_db
from routers.cart import get_current_user_id

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

def send_confirmation_email(username: str, order_id: int, total_amount: float):
    """
    Simulated email sending task
    """
    time.sleep(2) # Simulate network delay
    email_content = f"Hello {username},\nYour order #{order_id} has been placed successfully.\nTotal: ₹{total_amount}"
    print("\n--- NEW EMAIL ---")
    print(email_content)
    print("-----------------\n")

# User Order Operations
@router.post("/place", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)

def place_order(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Complex transaction to place an order:
    1. Read user cart
    2. Validate stock available
    3. Create order
    4. Create order items (with price snapshot)
    5. Reduce product stock
    6. Clear user cart
    """
    # 1. Read user cart
    cart_items = db.query(models.CartItem).filter(models.CartItem.user_id == user_id).all()
    order_services.validate_cart_not_empty(cart_items)

    # 2. Validate stock available and calculate total
    total_amount = 0
    order_items_to_create = []
    
    for item in cart_items:
        # 409 ERROR: Out of stock
        product = item.product
        order_services.validate_stock_sufficient(product, item.quantity)
        
        # Calculate amount
        item_total = product.price * item.quantity
        total_amount += item_total
        
        # Prepare order item data
        order_items_to_create.append({
            "product": product,
            "quantity": item.quantity,
            "price": product.price
        })

    # 3. Create the Order
    new_order = models.Order(
        user_id=user_id,
        total_amount=total_amount,
        status="placed" # Default status
    )
    db.add(new_order)
    db.flush() # Get the order ID without committing yet

    # 4. Create Order Items & 5. Reduce stock
    for item_data in order_items_to_create:
        # Create Order Item
        new_order_item = models.OrderItem(
            order_id=new_order.id,
            product_id=item_data["product"].id,
            quantity=item_data["quantity"],
            price=item_data["price"]
        )
        db.add(new_order_item)
        
        # Reduce Stock
        item_data["product"].stock -= item_data["quantity"]

    # 6. Clear user cart
    db.query(models.CartItem).filter(models.CartItem.user_id == user_id).delete()

    # Final commit for the entire transaction
    db.commit()
    db.refresh(new_order)
    
    # 7. Send confirmation email via background task
    user = db.query(models.User).filter(models.User.id == user_id).first()
    username = user.username if user else "Customer"
    
    background_tasks.add_task(
        send_confirmation_email,
        username=username,
        order_id=new_order.id,
        total_amount=new_order.total_amount
    )
    
    return new_order

@router.get("/", response_model=List[schemas.OrderResponse])
def get_my_orders(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Retrieve a list of orders placed by the current user.
    """
    orders = db.query(models.Order).filter(models.Order.user_id == user_id).all()
    return orders

@router.put("/cancel/{order_id}", response_model=schemas.OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Cancel an order:
    1. Validate order exists
    2. Validate ownership
    3. Validate status is 'placed'
    4. Restore stock
    5. Update status to 'cancelled'
    """
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    
    # Validation using services
    order_services.validate_order_exists(order)
    order_services.validate_order_ownership(order, user_id)
    order_services.validate_order_cancellable(order)

    # Restore stock for each item in the order
    for item in order.items:
        product = item.product
        product.stock += item.quantity
    
    # Update order status
    order.status = "cancelled"
    
    db.commit()
    db.refresh(order)
    
    return order
