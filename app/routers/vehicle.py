import logging
import os
from fastapi import APIRouter, Depends
from app.core.services import VehicleService
from app.core.models import Vehicle
from app.infrastructure.db import VehicleRepository, get_db
from app.infrastructure.cache import get_cahce
from motor.motor_asyncio import AsyncIOMotorClient
from utils import get_response

router = APIRouter()


error_logger = logging.getLogger("errorLogger")  # For error logs


# Dependency injection for VehicleService with the repository and cache
def get_vehicle_service():
    _, db = get_db()
    cache = get_cahce()
    vehicle_repo = VehicleRepository(db)
    return VehicleService(vehicle_repo, cache)


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

        return get_response(
            code="VEHICLE_ADDED",
            status=201,
            error=False,
            message="Vehicle added successfully",
            data={"vehicle_id": vehicle.vehicle_id},
        )

    except Exception as e:
        error_logger.error(f"Error adding vehicle: {e}")
        return get_response(
            status=400,
            error=True,
            code="INTERNAL_ERROR",
            message=str(e),
        )


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
    try:
        available_vehicles = await vehicle_service.get_available_vehicles()
        if not available_vehicles:
            return get_response(
                status=404,
                error=True,
                code="NO_VEHICLES",
                message="No available vehicles found",
            )
        return get_response(
            code="VEHICLES_AVAILABLE",
            status=200,
            error=False,
            message="List of available vehicles",
            data=available_vehicles,
        )
    except Exception as e:
        error_logger.error(f"Error fetching available vehicles: {e}")
        return get_response(
            status=400,
            error=True,
            code="INTERNAL_ERROR",
            message=str(e),
        )


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
        return get_response(
            code="VEHICLE_UPDATED",
            status=200,
            error=False,
            message="Vehicle details updated successfully",
        )
    except Exception as e:
        error_logger.error(f"Error updating vehicle: {e}")
        return get_response(
            status=400,
            error=True,
            code="INTERNAL_ERROR",
            message=str(e),
        )


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
    try:
        all_vehicles = await vehicle_service.get_all_vehicles()
        if not all_vehicles:
            return get_response(
                status=404,
                error=True,
                code="NO_VEHICLES",
                message="No vehicles found",
            )
        return get_response(
            code="VEHICLES_FOUND",
            status=200,
            error=False,
            message="List of all vehicles",
            data=all_vehicles,
        )
    except Exception as e:
        error_logger.error(f"Error fetching all vehicles: {e}")
        return get_response(
            status=400,
            error=True,
            code="INTERNAL_ERROR",
            message=str(e),
        )
