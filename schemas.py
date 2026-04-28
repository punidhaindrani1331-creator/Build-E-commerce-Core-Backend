from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List, Any, Generic, TypeVar

T = TypeVar("T")

# Standard Response Schemas
class Meta(BaseModel):
    page: Optional[int] = None
    limit: Optional[int] = None
    total: Optional[int] = None

class StandardResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    meta: Optional[Meta] = None

# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int = 0
    category: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None

class Product(ProductBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ProductSummary(BaseModel):
    id: int
    name: str
    price: float
    category: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class AdminCreate(UserCreate):
    admin_secret: str

class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class UserSummary(BaseModel):
    id: int
    username: str
    model_config = ConfigDict(from_attributes=True)


# Cart Schemas
class CartItemBase(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemCreate(CartItemBase):
    pass

class CartItem(BaseModel):
    id: int
    quantity: int
    product: ProductSummary
    model_config = ConfigDict(from_attributes=True)

class Cart(BaseModel):
    items: List[CartItem]
    total_price: float

# Order Schemas
class OrderItemResponse(BaseModel):
    id: int
    quantity: int
    price: float
    product: ProductSummary
    model_config = ConfigDict(from_attributes=True)

class OrderResponse(BaseModel):
    id: int
    user: UserSummary
    total_amount: float
    status: str
    created_at: datetime
    items: List[OrderItemResponse]
    model_config = ConfigDict(from_attributes=True)

# Report Schemas
class TopProductReport(BaseModel):
    product_id: int
    product_name: str
    total_quantity: int
    total_revenue: float

class SlowApiReport(BaseModel):
    endpoint: str
    response_time: float
