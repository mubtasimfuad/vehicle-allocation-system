from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from app.core.exceptions import DuplicateBookingError, VehicleUnavailableError
from app.core.services import AllocationService
from app.core.models import Allocation, UpdateAllocation
from app.infrastructure.db import AllocationRepository, VehicleRepository
from app.infrastructure.cache import RedisCache
from motor.motor_asyncio import AsyncIOMotorClient
import logging

# Initialize logging
logger = logging.getLogger(__name__)

router = APIRouter()
db_client = AsyncIOMotorClient("mongodb://localhost:27017")


# Dependency injection for AllocationService
def get_allocation_service():
    allocation_repo = AllocationRepository(db_client.vehicle_allocation_db)
    vehicle_repo = VehicleRepository(db_client.vehicle_allocation_db)
    cache = RedisCache(redis_url="redis://localhost:6379")
    return AllocationService(allocation_repo, vehicle_repo, cache, db_client)


# Endpoint to allocate a vehicle
@router.post("/allocate")
async def allocate_vehicle(
    allocation: Allocation,
    allocation_service: AllocationService = Depends(get_allocation_service),
):
    try:
        saved_allocation = await allocation_service.allocate_vehicle(
            allocation.employee_id,
            allocation.vehicle_id,
            allocation.from_datetime,
            allocation.to_datetime,
            allocation.purpose,
        )
        return {
            "message": "Vehicle allocated successfully",
            "allocation": saved_allocation,
        }
    except DuplicateBookingError as e:
        logger.warning(f"Duplicate booking error: {e}")
        raise HTTPException(status_code=409, detail=str(e))
    except VehicleUnavailableError as e:
        logger.warning(f"Vehicle unavailable: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error allocating vehicle: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.patch("/update/{allocation_id}")
async def update_allocation(
    allocation_id: str,
    update_data: UpdateAllocation,
    allocation_service: AllocationService = Depends(get_allocation_service),
):
    try:
        updated_allocation = await allocation_service.update_allocation(
            allocation_id=allocation_id,
            vehicle_id=update_data.vehicle_id,
            from_datetime=update_data.from_datetime,
            to_datetime=update_data.to_datetime,
            purpose=update_data.purpose,
        )
        return {
            "message": "Allocation updated successfully",
            "allocation": updated_allocation,
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating allocation: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred")


# Endpoint to get allocation history
@router.get("/history/{employee_id}")
async def get_allocation_history(
    employee_id: str,
    allocation_service: AllocationService = Depends(get_allocation_service),
):
    try:
        allocations = await allocation_service.get_allocation_history(employee_id)
        return allocations
    except Exception as e:
        logger.error(f"Error fetching allocation history: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/history")
async def get_allocation_history(
    employee_id: Optional[str] = None,
    vehicle_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    size: int = 10,
    allocation_service: AllocationService = Depends(get_allocation_service),
):
    """
    Fetch the allocation history based on provided filters.
    Pagination supported via 'page' and 'size'.
    """
    try:
        allocations, total_count = await allocation_service.get_filtered_allocations(
            employee_id=employee_id,
            vehicle_id=vehicle_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            size=size,
        )
        if not allocations:
            raise HTTPException(
                status_code=404, detail="No allocations found for the given filters"
            )

        # Return paginated response
        return {
            "total_count": total_count,
            "page": page,
            "size": size,
            "allocations": allocations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
