from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import time
from redis_client import redis_client

import models
from database import engine
from routers import product, cart, user, order, admin, report

# Initialize database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="E-commerce Core Backend",
    description="A clean and safe backend for e-commerce products.",
    version="1.0.0"
)

# Middleware to track response times
@app.middleware("http")
async def log_response_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Store the latest process time for this endpoint in Redis
    endpoint = f"{request.method} {request.url.path}"
    try:
        # We use a sorted set to keep track of endpoints and their times
        redis_client.zadd("reports:slow_apis", {endpoint: process_time})
    except Exception as e:
        print(f"Redis log_response_time error: {e}")
        
    response.headers["X-Process-Time"] = str(process_time)
    return response

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
        status_code=400,
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
app.include_router(report.router)

@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Welcome to the E-commerce Core Backend API"
    }
