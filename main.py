from fastapi import FastAPI
from app.routers import allocation, vehicle, user_role, report
from app.infrastructure.config import settings

app = FastAPI()

# Dynamically use environment settings
@app.get("/")
def read_root():
    return {
        "message": "Vehicle Allocation System",
        "environment": settings.ENV
    } 

# Include the routers for different parts of the    
app.include_router(allocation.router, prefix="/allocations", tags=["allocations"])
app.include_router(vehicle.router, prefix="/vehicles", tags=["vehicles"])
app.include_router(user_role.router, prefix="/roles", tags=["roles"])
app.include_router(report.router, prefix="/reports", tags=["reports"])
