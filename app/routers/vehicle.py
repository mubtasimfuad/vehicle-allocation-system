import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.services import VehicleService
from app.core.models import Vehicle
from app.infrastructure.db import VehicleRepository, get_db
from app.infrastructure.cache import RedisCache  # Import RedisCache
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter()

db_client = AsyncIOMotorClient("mongodb://localhost:27017")
error_logger = logging.getLogger("errorLogger")  # For error logs


# Dependency injection for VehicleService with the repository and cache
def get_vehicle_service():
    vehicle_repo = VehicleRepository(
        db_client.vehicle_allocation_db
    )  # Pass the db instance to the repository
    cache = RedisCache(redis_url="redis://localhost:6379")  # Initialize the cache instance
    return VehicleService(vehicle_repo, cache)  # Return the service with both vehicle_repo and cache


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
        print("Exception adding a vehicle: ", e)
        error_logger.error(f"Error adding vehicle: {e}")
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


# Endpoint to update vehicle
@router.patch(
    "/update/{vehicle_id}",
    # response_model=VehicleResponse,
    status_code=200,
    summary="Update vehicle details",
    description="Update the details of a vehicle in the system.",
    responses={
        200: {"description": "Vehicle details updated successfully"},
        400: {"description": "Invalid input data"},
    },
)
async def update_vehicle(
    vehicle_id: str,
    vehicle: Vehicle,
    vehicle_service: VehicleService = Depends(get_vehicle_service),
):
    """
    Update the details of a vehicle in the system.

    - **vehicle_id**: The ID of the vehicle to be updated.
    - **vehicle**: The updated details of the vehicle.
    - **returns**: Confirmation message.
    """
    try:
        vehicle.vehicle_id = vehicle_id
        await vehicle_service.update_vehicle(vehicle)
        return {"message": "Vehicle details updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# route for all vehicles
@router.get(
    "/all",
    # response_model=List[VehicleResponse],
    status_code=200,
    summary="Get all vehicles",
    description="Fetch a list of all vehicles in the system.",
    responses={
        200: {"description": "List of all vehicles"},
        404: {"description": "No vehicles found"},
    },
)
async def get_all_vehicles(
    vehicle_service: VehicleService = Depends(get_vehicle_service),
):
    """
    Retrieve a list of all vehicles.

    - **returns**: A list of all vehicles in the system.
    """
    all_vehicles = await vehicle_service.get_all_vehicles()
    if not all_vehicles:
        raise HTTPException(status_code=404, detail="No vehicles found")
    return all_vehicles
