from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.services import VehicleService
from app.core.models import Vehicle
from app.infrastructure.db import VehicleRepository, get_db
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter()

db_client = AsyncIOMotorClient("mongodb://localhost:27017")

# Dependency injection for VehicleService with the repository
def get_vehicle_service():
    vehicle_repo = VehicleRepository(db_client.vehicle_allocation_db)  # Pass the db instance to the repository
    return VehicleService(vehicle_repo)  # Return the service with the repository


@router.post(
    "/add",
    # response_model=VehicleResponse,
    status_code=201,
    summary="Add a new vehicle",
    description="Add a new vehicle to the system and return the vehicle ID.",
    responses={
        201: {"description": "Vehicle added successfully", "vehicle_id": "string"},
        400: {"description": "Invalid input data"},
    },
)
async def add_vehicle(
    vehicle: Vehicle,
    vehicle_service: VehicleService = Depends(get_vehicle_service),
):
    """
    Add a new vehicle to the system.

    - **vehicle**: The details of the vehicle to be added.
    - **returns**: The vehicle ID and confirmation message.
    """
    try:
        await vehicle_service.add_vehicle(vehicle)
        return {
            "message": "Vehicle added successfully",
            "vehicle_id": vehicle.vehicle_id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/available",
    # response_model=List[VehicleResponse],
    status_code=200,
    summary="Get all available vehicles",
    description="Fetch a list of all vehicles that are currently available in the system.",
    responses={
        200: {"description": "List of available vehicles"},
        404: {"description": "No available vehicles found"},
    },
)
async def get_available_vehicles(
    vehicle_service: VehicleService = Depends(get_vehicle_service),
):
    """
    Retrieve a list of available vehicles.

    - **returns**: A list of vehicles that are available.
    """
    available_vehicles = await vehicle_service.get_available_vehicles()
    if not available_vehicles:
        raise HTTPException(status_code=404, detail="No available vehicles found")
    return available_vehicles
