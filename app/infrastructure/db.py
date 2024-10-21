from motor.motor_asyncio import AsyncIOMotorClient
from app.core.models import Allocation, Vehicle


class AllocationRepository:
    def __init__(self, db):
        self.db = db

    async def save_allocation(self, allocation: Allocation):
        await self.db.allocations.insert_one(allocation.dict())

    async def get_allocations_by_employee(self, employee_id: str):
        return await self.db.allocations.find({"employee_id": employee_id}).to_list(100)

    async def get_vehicle_by_id(self, vehicle_id: str):
        return await self.db.vehicles.find_one({"vehicle_id": vehicle_id})


class VehicleRepository:
    def __init__(self, db):
        self.db = db

    async def get_vehicles_by_status(self, status: str):
        return await self.db.vehicles.find({"status": status}).to_list(100)

    async def update_vehicle(self, vehicle: Vehicle):
        await self.db.vehicles.update_one(
            {"vehicle_id": vehicle.vehicle_id}, {"$set": vehicle.dict()}
        )
