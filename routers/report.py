from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

import schemas, models
from services import report_services
from database import get_db
from auth import get_current_admin

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

@router.get("/top-products", response_model=schemas.StandardResponse[List[schemas.TopProductReport]])
def view_top_products(
    limit: int = 5,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """
    Retrieve top selling products. Restricted to Admin.
    """
    top_products = report_services.get_top_selling_products(db, limit=limit)
    
    # Format the data for the response
    formatted_data = []
    for item in top_products:
        formatted_data.append({
            "product_id": item.product_id,
            "product_name": item.product_name,
            "total_quantity": int(item.total_quantity),
            "total_revenue": float(item.total_revenue)
        })
        
    return {
        "success": True,
        "message": "Top products report generated",
        "data": formatted_data
    }

@router.get("/slow-apis", response_model=schemas.StandardResponse[List[schemas.SlowApiReport]])
def view_slow_apis(
    limit: int = 10,
    admin: models.User = Depends(get_current_admin)
):
    """
    Retrieve slowest APIs based on tracked response times. Restricted to Admin.
    """
    slow_apis = report_services.get_slow_apis(limit=limit)
    
    formatted_data = []
    for endpoint, response_time in slow_apis:
        formatted_data.append({
            "endpoint": endpoint,
            "response_time": float(response_time)
        })
        
    return {
        "success": True,
        "message": "Slow APIs report generated",
        "data": formatted_data
    }
