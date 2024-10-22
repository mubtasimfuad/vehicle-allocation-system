import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.exceptions import DuplicateBookingError, VehicleUnavailableError
from app.core.models import Allocation, UpdateAllocation, Vehicle
from datetime import datetime
from typing import List, Optional

from app.infrastructure.db import VehicleRepository

# Set up logging
logger = logging.getLogger(__name__)


class AllocationService:
    def __init__(self, allocation_repo, vehicle_repo, cache, db_client):
        self.allocation_repo = allocation_repo
        self.vehicle_repo = vehicle_repo
        self.cache = cache
        self.db_client = db_client  # Shared MongoDB client

    async def check_employee_booking(self, employee_id: str, booking_date: str):
        try:
            cached_booking = await self.cache.get(
                f"employee:{employee_id}:booking:{booking_date}"
            )
            if cached_booking:
                logger.info(
                    f"Cache hit for employee booking: {employee_id}, date: {booking_date}"
                )
                return cached_booking

            existing_booking = (
                await self.allocation_repo.get_allocation_by_employee_and_date(
                    employee_id, booking_date
                )
            )
            if existing_booking:
                await self.cache.set(
                    f"employee:{employee_id}:booking:{booking_date}", existing_booking
                )
                logger.info(
                    f"Booking found and cached for employee: {employee_id} on {booking_date}"
                )
            return existing_booking
        except Exception as e:
            logger.error(f"Error checking employee booking: {e}")
            raise

    async def check_vehicle_availability(self, vehicle_id: str):
        try:
            cached_vehicle_status = await self.cache.get(f"vehicle:{vehicle_id}:status")
            if cached_vehicle_status == "allocated":
                logger.warning(f"Duplicate booking attempt for vehicle {vehicle_id}")
                raise DuplicateBookingError(
                    f"Vehicle {vehicle_id} is already allocated"
                )

            vehicle = await self.vehicle_repo.get_vehicle_by_id(vehicle_id)
            if not vehicle or vehicle.status != "available":
                logger.warning(f"Vehicle {vehicle_id} is not available")
                raise VehicleUnavailableError(f"Vehicle {vehicle_id} is not available")

            await self.cache.set(f"vehicle:{vehicle_id}:status", vehicle.status)
            logger.info(f"Vehicle {vehicle_id} status cached as {vehicle.status}")
            return vehicle
        except Exception as e:
            logger.error(f"Error checking vehicle availability: {e}")
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
                logger.error(
                    f"Duplicate booking detected for employee {employee_id} on {from_datetime}"
                )
                raise DuplicateBookingError(
                    f"Employee {employee_id} already has a booking for that day."
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

            await self.cache.delete(f"vehicle:{vehicle_id}:status")
            await self.cache.delete(f"employee:{employee_id}:booking:{from_datetime}")
            logger.info(
                f"Vehicle {vehicle_id} allocated to employee {employee_id} successfully"
            )
            return allocation
        except (DuplicateBookingError, VehicleUnavailableError) as e:
            logger.warning(f"Business rule violation: {e}")
            raise
        except Exception as e:
            logger.error(f"Error allocating vehicle: {e}")
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
                        logger.error(f"Allocation {allocation_id} not found")
                        raise ValueError(f"Allocation {allocation_id} not found.")

                    # Convert allocation_data (dict) into an Allocation object
                    allocation = Allocation(**allocation_data)
                    print("allocation", allocation)

                    # Check if the allocation is pending and can be modified
                    if allocation.status != "pending":
                        logger.warning(
                            f"Attempted to update non-pending allocation: {allocation_id}"
                        )
                        raise ValueError(
                            "Allocation is already approved and cannot be modified."
                        )


                    # Check vehicle availability if the vehicle is being changed
                    if vehicle_id and vehicle_id != allocation.vehicle_id:
                        await self.check_vehicle_availability(vehicle_id)



                    # Update the allocation fields
                    if vehicle_id:
                        allocation.vehicle_id = vehicle_id
                    if from_datetime:
                        allocation.from_datetime = from_datetime
                    if to_datetime:
                        allocation.to_datetime = to_datetime
                    if purpose:
                        allocation.purpose = purpose

                    # Convert the updated allocation object back to a dictionary before saving
                    allocation_dict = allocation.dict(by_alias=True)
                    print("vehicle_id 2", vehicle_id)


                    await self.allocation_repo.update_allocation(
                        allocation_dict, session=session
                    )
                    logger.info(f"Allocation {allocation_id} updated successfully")

                    # Invalidate cache after update
                    await self.cache.delete(
                        f"employee:{allocation.employee_id}:booking:{allocation.from_datetime}"
                    )
                    await self.cache.delete(f"vehicle:{allocation.vehicle_id}:status")

            return allocation
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating allocation: {e}")
            raise

    async def get_allocation_history(self, employee_id: str) -> List[Allocation]:
        try:
            allocations = await self.allocation_repo.get_allocations_by_employee(
                employee_id
            )
            logger.info(f"Fetched allocation history for employee {employee_id}")
            return allocations
        except Exception as e:
            logger.error(
                f"Error fetching allocation history for employee {employee_id}: {e}"
            )
            raise


class VehicleService:
    def __init__(self, vehicle_repo: VehicleRepository):
        self.vehicle_repo = vehicle_repo  # Inject the repository

    def get_available_vehicles(self) -> List[Vehicle]:
        return self.vehicle_repo.get_vehicles_by_status("available")

    async def add_vehicle(self, vehicle: Vehicle):
        await self.vehicle_repo.add_vehicle(vehicle)

    async def update_vehicle_status(self, vehicle_id: str, status: str):
        vehicle = await self.vehicle_repo.get_vehicle_by_id(vehicle_id)
        vehicle.status = status
        await self.vehicle_repo.update_vehicle(vehicle)
