import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from app.core.exceptions import DuplicateBookingError, VehicleUnavailableError
from app.core.services import AllocationService
from app.core.models import Allocation, UpdateAllocation
from app.infrastructure.db import AllocationRepository, VehicleRepository, get_db
from app.infrastructure.cache import get_cahce
from motor.motor_asyncio import AsyncIOMotorClient
from utils import get_response
import logging

# Initialize logging
logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency injection for AllocationService
def get_allocation_service():
    db_client, db = get_db()
    cache = get_cahce()
    allocation_repo = AllocationRepository(db)
    vehicle_repo = VehicleRepository(db)
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
        return get_response(
            code="ALLOCATED",
            status=200,
            error=False,
            message="Vehicle allocated successfully",
            data={"allocation": saved_allocation},
        )

    except DuplicateBookingError as e:
        logger.warning(f"Duplicate booking error: {e}")
        return get_response(
            status=409,
            error=True,
            code="DUPLICATE_BOOKING",
            message=str(e),
        )
    except VehicleUnavailableError as e:
        logger.warning(f"Vehicle unavailable: {e}")
        return get_response(
            status=409,
            error=True,
            code="VEHICLE_UNAVAILABLE",
            message=str(e),
        )
    except Exception as e:
        logger.error(f"Error allocating vehicle: {e}")
        return get_response(
            status=500,
            error=True,
            code="INTERNAL_ERROR",
            message="An internal error occurred",
        )


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
        return get_response(
            code="VEHICLE_UPDATED",
            status=200,
            error=False,
            message="Allocation updated successfully",
            data={"allocation": updated_allocation},
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return get_response(
            status=400, error=True, code="VALIDATION_ERROR", message=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating allocation: {e}")
        return get_response(
            status=500,
            error=True,
            code="INTERNAL_ERROR",
            message="An internal error occurred",
        )


# # Endpoint to get allocation history
# @router.get("/history/{employee_id}")
# async def get_allocation_history(
#     employee_id: str,
#     allocation_service: AllocationService = Depends(get_allocation_service),
# ):
#     try:
#         allocations = await allocation_service.get_allocation_history(employee_id)
#         return allocations
#     except Exception as e:
#         logger.error(f"Error fetching allocation history: {e}")
#         raise HTTPException(status_code=500, detail="An internal error occurred")


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
            return get_response(
                status=404,
                error=True,
                code="NOT_FOUND",
                message="No allocations found for the given filters",
            )

        # Return paginated response
        return get_response(
            code="ALLOCATIONS_FOUND",
            status=200,
            error=False,
            message="Allocations found",
            data={
                "total_count": total_count,
                "page": page,
                "size": size,
                "allocations": allocations,
            },
        )

    except Exception as e:
        return get_response(
            status=500,
            error=True,
            code="INTERNAL_ERROR",
            message="An internal error occurred",
        )
