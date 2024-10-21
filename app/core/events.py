from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime

class VehicleBookedEvent(BaseModel):
    event_id: str = str(uuid4())
    vehicle_id: str
    employee_id: str
    timestamp: str = datetime.utcnow().isoformat()
    mileage: float
    purpose: str

class VehicleMaintenanceEvent(BaseModel):
    event_id: str = str(uuid4())
    vehicle_id: str
    start_date: str
    end_date: str
    reason: str
