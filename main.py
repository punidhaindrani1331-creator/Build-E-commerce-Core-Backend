from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

import models
from database import engine
from routers import product, cart, user, order, admin

# Initialize database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="E-commerce Core Backend",
    description="A clean and safe backend for e-commerce products.",
    version="1.0.0"
)

# Custom Exception Handlers for Standard Response Format
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            "data": exc.errors()
        }
    )

# Register routers
app.include_router(product.router)
app.include_router(cart.router)
app.include_router(user.router)
app.include_router(order.router)
app.include_router(admin.router)

@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Welcome to the E-commerce Core Backend API"
    }
