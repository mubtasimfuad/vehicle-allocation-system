import logging
from app.core.exceptions import DuplicateBookingError, VehicleUnavailableError
from app.core.models import Allocation, Vehicle
from datetime import datetime
from typing import List, Optional, Tuple

from app.infrastructure.db import VehicleRepository

# Set up logging
general_logger = logging.getLogger("appLogger")  # For general logs
error_logger = logging.getLogger("errorLogger")  # For error logs


class AllocationService:
    def __init__(self, allocation_repo, vehicle_repo, cache, db_client):
        self.allocation_repo = allocation_repo
        self.vehicle_repo = vehicle_repo
        self.cache = cache
        self.db_client = db_client  # Shared MongoDB client

    async def get_filtered_allocations(
        self,
        employee_id: Optional[str] = None,
        vehicle_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,  # Pagination parameter
        size: int = 10,  # Pagination parameter
    ) -> Tuple[List[Allocation], int]:  # Return allocations and total count
        cache_key = (
            f"history:{employee_id}:{vehicle_id}:{start_date}:{end_date}:{page}:{size}"
        )

        # Check cache first
        cached_allocations = await self.cache.get(cache_key)
        if cached_allocations:
            general_logger.info(f"Cache hit for key: {cache_key}")
            # Ensure cached result is a tuple with exactly two values (allocations, total_count)
            if isinstance(cached_allocations, tuple) and len(cached_allocations) == 2:
                return cached_allocations

        # Build query dynamically based on filters
        query = {}
        if employee_id:
            query["employee_id"] = employee_id
        if vehicle_id:
            query["vehicle_id"] = vehicle_id
        if start_date or end_date:
            query["from_datetime"] = {}
            if start_date:
                query["from_datetime"]["$gte"] = datetime.fromisoformat(start_date)
            if end_date:
                query["from_datetime"]["$lte"] = datetime.fromisoformat(end_date)

        # Pagination setup
        skip = (page - 1) * size

        # Query DB with pagination
        allocations = await self.allocation_repo.get_allocations_by_filter(
            query, skip=skip, limit=size
        )
        total_count = await self.allocation_repo.get_count(query)

        # Ensure to return a tuple with exactly two elements
        result = (allocations, total_count)

        # Cache the result for future requests, expires in 1 hour (3600 seconds)
        await self.cache.set(cache_key, result, expiration=3600)
        general_logger.info(f"Cache set for key: {cache_key} with expiration in 1 hour")

        return result

    async def check_employee_booking(self, employee_id: str, booking_date: str):
        cache_key = f"employee:{employee_id}:booking:{booking_date}"
        cached_booking = await self.cache.get(cache_key)
        if cached_booking:
            general_logger.info(
                f"Cache hit for employee booking: {employee_id}, date: {booking_date}"
            )
            return cached_booking

        # Fetch from DB if not in cache
        existing_booking = (
            await self.allocation_repo.get_allocation_by_employee_and_date(
                employee_id, booking_date
            )
        )
        if existing_booking:
            await self.cache.set(cache_key, existing_booking, expiration=3600)
            general_logger.info(
                f"Cache set for employee booking: {employee_id} on {booking_date}"
            )
        return existing_booking

    async def check_vehicle_availability(self, vehicle_id: str):
        try:
            cached_vehicle_status = await self.cache.get(f"vehicle:{vehicle_id}:status")
            if cached_vehicle_status == "allocated":
                general_logger.warning(
                    f"Duplicate booking attempt for vehicle {vehicle_id}"
                )
                raise DuplicateBookingError(
                    f"Vehicle {vehicle_id} is already allocated"
                )

            vehicle = await self.vehicle_repo.get_vehicle_by_id(vehicle_id)
            if not vehicle or vehicle.status != "available":
                general_logger.warning(f"Vehicle {vehicle_id} is not available")
                raise VehicleUnavailableError(f"Vehicle {vehicle_id} is not available")

            await self.cache.set(f"vehicle:{vehicle_id}:status", vehicle.status)
            general_logger.info(
                f"Vehicle {vehicle_id} status cached as {vehicle.status}"
            )
            return vehicle
        except Exception as e:
            error_logger.error(f"Error checking vehicle availability: {e}")
            raise

    async def allocate_vehicle(
        self,
        employee_id: str,
        vehicle_id: str,
        from_datetime: str,
        to_datetime: str,
        purpose: str,
    ):
        try:
            existing_booking = await self.check_employee_booking(
                employee_id, from_datetime
            )
            if existing_booking:
                raise DuplicateBookingError(
                    f"Employee {employee_id} already has a booking on {from_datetime}"
                )

            vehicle = await self.check_vehicle_availability(vehicle_id)

            async with await self.db_client.start_session() as session:
                async with session.start_transaction():
                    vehicle.status = "allocated"
                    await self.vehicle_repo.update_vehicle(vehicle, session=session)

                    allocation = Allocation(
                        employee_id=employee_id,
                        vehicle_id=vehicle_id,
                        from_datetime=from_datetime,
                        to_datetime=to_datetime,
                        purpose=purpose,
                    )
                    await self.allocation_repo.save_allocation(
                        allocation, session=session
                    )

            # Invalidate caches related to vehicle and employee booking
            await self.cache.delete(f"vehicle:{vehicle_id}:status")
            await self.cache.delete(f"employee:{employee_id}:booking:{from_datetime}")
            await self.cache.delete_pattern(
                f"history:*"
            )  # Invalidate all history cache entries
            general_logger.info(
                f"Vehicle {vehicle_id} allocated to employee {employee_id}, cache invalidated"
            )

            return allocation
        except (DuplicateBookingError, VehicleUnavailableError) as e:
            general_logger.warning(f"Business rule violation: {e}")
            error_logger.error(f"Allocation error: {e}")
            raise
        except Exception as e:
            error_logger.error(f"Unexpected error during allocation: {e}")
            raise

    async def update_allocation(
        self,
        allocation_id: str,
        vehicle_id: Optional[str] = None,
        from_datetime: Optional[datetime] = None,
        to_datetime: Optional[datetime] = None,
        purpose: Optional[str] = None,
    ):
        try:
            async with await self.db_client.start_session() as session:
                async with session.start_transaction():
                    allocation_data = await self.allocation_repo.get_allocation_by_id(
                        allocation_id, session=session
                    )
                    if not allocation_data:
                        raise ValueError(f"Allocation {allocation_id} not found.")

                    allocation = Allocation(**allocation_data)

                    if allocation.status != "pending":
                        raise ValueError(
                            "Allocation is already approved and cannot be modified."
                        )

                    if vehicle_id and vehicle_id != allocation.vehicle_id:
                        await self.check_vehicle_availability(vehicle_id)

                    # Update allocation fields
                    if vehicle_id:
                        allocation.vehicle_id = vehicle_id
                    if from_datetime:
                        allocation.from_datetime = from_datetime
                    if to_datetime:
                        allocation.to_datetime = to_datetime
                    if purpose:
                        allocation.purpose = purpose

                    await self.allocation_repo.update_allocation(
                        allocation.dict(by_alias=True), session=session
                    )

                    # Invalidate caches after update
                    await self.cache.delete(
                        f"employee:{allocation.employee_id}:booking:{allocation.from_datetime}"
                    )
                    await self.cache.delete(f"vehicle:{allocation.vehicle_id}:status")
                    await self.cache.delete_pattern(
                        f"history:*"
                    )  # Invalidate history cache
                    general_logger.info(
                        f"Allocation {allocation_id} updated, cache invalidated"
                    )

            return allocation
        except ValueError as e:
            error_logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            error_logger.error(f"Error updating allocation: {e}")
            raise

    async def get_allocation_history(self, employee_id: str) -> List[Allocation]:
        try:
            allocations = await self.allocation_repo.get_allocations_by_employee(
                employee_id
            )
            general_logger.info(
                f"Fetched allocation history for employee {employee_id}"
            )
            return allocations
        except Exception as e:
            error_logger.error(
                f"Error fetching allocation history for employee {employee_id}: {e}"
            )
            raise


class VehicleService:
    def __init__(self, vehicle_repo: VehicleRepository, cache):
        self.vehicle_repo = vehicle_repo  # Inject the repository
        self.cache = cache

    async def get_available_vehicles(self) -> List[Vehicle]:
        return await self.vehicle_repo.get_vehicles_by_status("available")

    async def get_all_vehicles(self) -> List[Vehicle]:
        return await self.vehicle_repo.get_all_vehicles()

    async def add_vehicle(self, vehicle: Vehicle):
        if not vehicle.current_driver_id and vehicle.status == "available":
            raise ValueError("A vehicle must have a driver if it is available.")

        await self.vehicle_repo.add_vehicle(vehicle)
        # Invalidate cache for vehicle and history
        await self.cache.delete(f"vehicle:{vehicle.vehicle_id}:status")
        await self.cache.delete_pattern(f"history:*")  # Invalidate history cache

    async def update_vehicle(self, vehicle: Vehicle):
        if not vehicle.current_driver_id and vehicle.status == "available":
            raise ValueError("A vehicle must have a driver if it is available.")
        await self.vehicle_repo.update_vehicle(vehicle)
        # Invalidate cache for vehicle and history
        await self.cache.delete(f"vehicle:{vehicle.vehicle_id}:status")
        await self.cache.delete_pattern(f"history:*")  # Invalidate history cache

    async def update_vehicle_status(self, vehicle_id: str, status: str):
        vehicle = await self.vehicle_repo.get_vehicle_by_id(vehicle_id)
        vehicle.status = status
        await self.vehicle_repo.update_vehicle(vehicle)
        # Invalidate cache after status update
        await self.cache.delete(f"vehicle:{vehicle_id}:status")
        await self.cache.delete_pattern(f"history:*")  # Invalidate history cache
