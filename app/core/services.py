from typing import List
from app.core.models import Allocation, Vehicle, Employee

class AllocationService:
    def __init__(self, allocation_repo, event_publisher):
        self.allocation_repo = allocation_repo  # Dependency injection for allocation repository (MongoDB)
        self.event_publisher = event_publisher  # Dependency injection for publishing events

    def allocate_vehicle(self, employee_id: str, vehicle_id: str, date: str, purpose: str) -> Allocation:
        # Logic to allocate a vehicle to an employee
        vehicle = self.allocation_repo.get_vehicle_by_id(vehicle_id)
        if vehicle.status == "available":
            allocation = Allocation(employee_id=employee_id, vehicle_id=vehicle_id, date=date, purpose=purpose, status="pending")
            self.allocation_repo.save_allocation(allocation)
            self.event_publisher.publish_vehicle_booked_event(allocation)
            return allocation
        else:
            raise Exception("Vehicle is not available")

    def get_allocations_by_employee(self, employee_id: str) -> List[Allocation]:
        return self.allocation_repo.get_allocations_by_employee(employee_id)

class VehicleService:
    def __init__(self, vehicle_repo):
        self.vehicle_repo = vehicle_repo  # Dependency injection for vehicle repository

    def get_available_vehicles(self) -> List[Vehicle]:
        return self.vehicle_repo.get_vehicles_by_status("available")

    def update_vehicle_status(self, vehicle_id: str, status: str):
        vehicle = self.vehicle_repo.get_vehicle_by_id(vehicle_id)
        vehicle.status = status
        self.vehicle_repo.update_vehicle(vehicle)
