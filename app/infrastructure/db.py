import logging
import os
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.models import Allocation, Vehicle
# Set up logging
general_logger = logging.getLogger("appLogger")  # For general logs
error_logger = logging.getLogger("errorLogger")  # For error logs



def get_db():
    """Return the MongoDB database object"""
    # Get MongoDB connection details from environment variables
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/vehicle_allocation_db?rplicaSet=rs0")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "vehicle_allocation_db")
    general_logger.info(f"Connecting to MongoDB at {MONGO_URI}...")
    # MongoDB Client
    db_client = AsyncIOMotorClient(MONGO_URI)
    db = db_client[MONGO_DB_NAME]
    return db_client, db


class AllocationRepository:
    def __init__(self, db):
        self.db = db

    async def get_allocations_by_filter(
        self, query: dict, skip: int = 0, limit: int = 10
    ) -> List[Allocation]:
        # Perform the paginated query
        allocations = (
            await self.db.allocations.find(query).skip(skip).limit(limit).to_list(limit)
        )
        for allocation in allocations:
            allocation["_id"] = str(allocation["_id"])  # Convert ObjectId to string
        return allocations

    async def get_count(self, query: dict) -> int:
        # Get the total count of documents matching the query (for pagination)
        return await self.db.allocations.count_documents(query)

    async def save_allocation(self, allocation: Allocation, session=None):
        allocation_data = allocation.dict(by_alias=True)
        await self.db.allocations.insert_one(allocation_data, session=session)

    async def get_allocation_by_employee_and_date(
        self, employee_id: str, booking_date: str
    ):
        allocation = await self.db.allocations.find_one(
            {
                "employee_id": employee_id,
                "from_datetime": {"$lte": booking_date},
                "to_datetime": {"$gte": booking_date},
            }
        )
        if allocation:
            allocation["_id"] = str(allocation["_id"])
        return allocation

    async def get_allocations_by_employee(self, employee_id: str):
        allocations = await self.db.allocations.find(
            {"employee_id": employee_id}
        ).to_list(100)
        for allocation in allocations:
            allocation["_id"] = str(allocation["_id"])  # Convert ObjectId to string
        return allocations

    async def get_allocation_by_id(self, allocation_id: str, session=None):
        allocation = await self.db.allocations.find_one(
            {"allocation_id": allocation_id},
            session=session,  # Ensure the session is passed
        )
        if allocation:
            allocation["_id"] = str(allocation["_id"])
        return allocation

    async def update_allocation(self, allocation: dict, session=None):
        if "_id" in allocation:
            del allocation["_id"]
        await self.db.allocations.update_one(
            {"allocation_id": allocation["allocation_id"]},
            {"$set": allocation},
            session=session,  # Ensure the session is passed
        )


class VehicleRepository:
    def __init__(self, db):
        self.db = db

    async def add_vehicle(self, vehicle: Vehicle, session=None):
        vehicle_data = vehicle.dict(by_alias=True)
        await self.db.vehicles.insert_one(vehicle_data, session=session)

    async def get_vehicle_by_id(self, vehicle_id: str, session=None) -> Vehicle:
        vehicle_data = await self.db.vehicles.find_one(
            {"vehicle_id": vehicle_id}, session=session  # Ensure the session is passed
        )
        if vehicle_data:
            vehicle_data["_id"] = str(vehicle_data["_id"])
            return Vehicle(**vehicle_data)
        return None

    async def update_vehicle(self, vehicle: Vehicle, session=None):
        vehicle_data = vehicle.dict(by_alias=True)
        if "_id" in vehicle_data:
            del vehicle_data["_id"]
        await self.db.vehicles.update_one(
            {"vehicle_id": vehicle_data["vehicle_id"]},
            {"$set": vehicle_data},
            session=session,  # Ensure the session is passed
        )

    async def get_vehicles_by_status(self, status: str):
        vehicles = await self.db.vehicles.find({"status": status}).to_list(100)
        for vehicle in vehicles:
            vehicle["_id"] = str(vehicle["_id"])
        return vehicles

    async def get_all_vehicles(self):
        vehicles = await self.db.vehicles.find().to_list(100)
        for vehicle in vehicles:
            vehicle["_id"] = str(vehicle["_id"])
        return vehicles
