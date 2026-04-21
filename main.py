from fastapi import FastAPI
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

# Register routers
app.include_router(product.router)
app.include_router(cart.router)
app.include_router(user.router)
app.include_router(order.router)
app.include_router(admin.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the E-commerce Core Backend API"}
