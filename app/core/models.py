from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo, validator
from typing import Optional, get_type_hints
from uuid import uuid4
from enum import Enum


class Role(str, Enum):
    EMPLOYEE = "employee"
    DRIVER = "driver"
    ADMIN = "admin"


class VehicleStatus(str, Enum):
    AVAILABLE = "available"
    IN_MAINTENANCE = "in_maintenance"
    BOOKED = "booked"


class AllocationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class EventTypes(str, Enum):
    BOOKING = "booking"
    MAINTENANCE = "maintenance"
    CANCELLATION = "cancellation"
    APPROVAL = "approval"
    REJECTION = "rejection"
    ALLOCATION = "allocation"


class Employee(BaseModel):
    employee_id: str
    name: str
    role: str = Role.EMPLOYEE
    email = str 


class Vehicle(BaseModel):
    vehicle_id: str = Field(default_factory=lambda: str(uuid4()))
    current_driver_id: Optional[str] = None
    status: str = VehicleStatus.AVAILABLE
    fuel_efficiency: float  # Mileage in miles per gallon (or km/liter)
    make: str
    model: str
    capacity: int


class Allocation(BaseModel):
    allocation_id: str = Field(default_factory=lambda: str(uuid4()))
    employee_id: str
    vehicle_id: str
    from_datetime: datetime
    to_datetime: datetime
    purpose: Optional[str] = None
    status: Optional[str] = "pending"

    # Field-level validation for 'from_datetime' and 'to_datetime'
    @field_validator("from_datetime", "to_datetime", mode="before")
    def parse_and_convert_to_utc(cls, value):
        """Ensures that datetime fields are timezone-aware and converted to UTC."""
        if isinstance(value, str):
            # Convert 'Z' to '+00:00' to handle Zulu time format (UTC)
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            try:
                parsed_datetime = datetime.fromisoformat(value)
                return parsed_datetime.astimezone(timezone.utc)
            except ValueError:
                raise ValueError(f"Invalid datetime format: {value}")
        elif isinstance(value, datetime):
            # Ensure that the datetime is timezone-aware
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return value

    # Ensure from_datetime is before to_datetime
    @validator("to_datetime")
    def check_from_before_to(cls, to_datetime, values):
        from_datetime = values.get("from_datetime")
        if from_datetime and from_datetime >= to_datetime:
            raise ValueError("from_datetime must be earlier than to_datetime.")
        return to_datetime
    @validator("from_datetime")
    def check_from_before_to(cls, from_datetime, values):
        to_datetime = values.get("to_datetime")
        if to_datetime and from_datetime >= to_datetime or from_datetime <= datetime.now(timezone.utc):
            raise ValueError("from_datetime must be earlier than to_datetime and in the future.")
        return from_datetime


class UpdateAllocation(BaseModel):
    vehicle_id: Optional[str] = None
    from_datetime: Optional[datetime] = None
    to_datetime: Optional[datetime] = None
    purpose: Optional[str] = None

    @model_validator(mode="after")
    def check_dates(cls, values: ValidationInfo):
        """Cross-field validation to ensure from_datetime is in the future and before to_datetime."""
        from_datetime = values.from_datetime
        to_datetime = values.to_datetime

        # Convert current time to an aware UTC datetime
        now_utc = datetime.now(timezone.utc)

        # Ensure from_datetime is timezone-aware; if naive, make it UTC
        if from_datetime and from_datetime.tzinfo is None:
            from_datetime = from_datetime.replace(tzinfo=timezone.utc)

        # Ensure old allocations cannot be modified
        if from_datetime and from_datetime <= now_utc:
            raise ValueError("Past allocations cannot be modified.")

        # Ensure from_datetime is before to_datetime
        if from_datetime and to_datetime:
            if to_datetime.tzinfo is None:
                to_datetime = to_datetime.replace(tzinfo=timezone.utc)
            if from_datetime >= to_datetime:
                raise ValueError("from_datetime must be earlier than to_datetime.")

        return values

    # Field-level validation to ensure proper parsing
    @field_validator("from_datetime", "to_datetime", mode="before")
    def parse_dates(cls, value):
        """Ensures that datetime fields are properly parsed, including UTC 'Z' format."""
        if isinstance(value, str):
            if value.endswith("Z"):
                value = (
                    value[:-1] + "+00:00"
                )  # Convert 'Z' to '+00:00' for compatibility with ISO format
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                raise ValueError(f"Invalid datetime format for value: {value}")
        return value


class Event(BaseModel):
    event_id: str = str(uuid4())
    event_type: str  # e.g., "BOOKING", "MAINTENANCE", "CANCELLATION"
    timestamp: str
    employee_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    details: Optional[dict] = {}  # Store additional event details as needed
