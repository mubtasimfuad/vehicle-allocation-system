from pydantic import BaseModel
from typing import Optional, List
from uuid import uuid4

class Employee(BaseModel):
    employee_id: str
    name: str
    role: str = "employee"  # Default role is employee, can be driver or admin
    frequent_vehicles: Optional[List[str]] = []
    frequent_drivers: Optional[List[str]] = []

class Vehicle(BaseModel):
    vehicle_id: str
    driver_id: Optional[str] = None
    status: str  # available, in_maintenance, booked
    mileage: float
    fuel_efficiency: float  # Mileage in miles per gallon (or km/liter)
    
class Allocation(BaseModel):
    allocation_id: str = str(uuid4())  # Generate unique allocation ID
    employee_id: str
    vehicle_id: str
    driver_id: Optional[str]
    date: str
    mileage: Optional[float] = None
    purpose: Optional[str] = None
    status: str  # pending, confirmed, canceled
    
class Event(BaseModel):
    event_id: str = str(uuid4())
    event_type: str  # e.g., "BOOKING", "MAINTENANCE", "CANCELLATION"
    timestamp: str
    employee_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    details: Optional[dict] = {}  # Store additional event details as needed
