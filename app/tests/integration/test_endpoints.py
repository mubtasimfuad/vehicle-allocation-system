import pytest
from httpx import AsyncClient
from main import app
from app.core.models import Vehicle, Allocation
from datetime import datetime, timedelta
import uuid  # To generate unique IDs for each test session

@pytest.mark.asyncio
async def test_vehicle_allocation_flow():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        
        # Generate unique IDs for this session
        unique_employee_id = f"emp_{uuid.uuid4()}"
        unique_vehicle_id = str(uuid.uuid4())
        unique_driver_id = f"driver_{uuid.uuid4()}"  # New driver ID
        
        # 1. Add a new vehicle with a unique vehicle ID and driver
        vehicle_data = {
            "vehicle_id": unique_vehicle_id,
            "make": "Toyota",
            "model": "Camry",
            "capacity": 5,
            "fuel_efficiency": 25.0,
            "current_driver_id": unique_driver_id  # Include driver ID
        }

        response = await client.post("/vehicles/add", json=vehicle_data)
        assert response.status_code == 201
        vehicle_id = response.json()['data']['vehicle_id']
        assert vehicle_id == unique_vehicle_id  # Ensure the vehicle ID matches what we set

        # 2. Update the vehicle
        updated_vehicle_data = {
            "vehicle_id": vehicle_id,
            "make": "Toyota",
            "model": "Camry XLE",
            "capacity": 5,
            "fuel_efficiency": 26.0,
            "current_driver_id": unique_driver_id  # Keep the same driver ID
        }

        response = await client.patch(f"/vehicles/update/{vehicle_id}", json=updated_vehicle_data)
        assert response.status_code == 200
        assert response.json()['code'] == "VEHICLE_UPDATED"

        # 3. Allocate the vehicle
        allocation_data = {
            "employee_id": unique_employee_id,
            "vehicle_id": vehicle_id,
            "from_datetime": (datetime.now() + timedelta(days=1)).isoformat(),
            "to_datetime": (datetime.now() + timedelta(days=2)).isoformat(),
            "purpose": "Business trip"
        }

        response = await client.post("/allocations/allocate", json=allocation_data)
        assert response.status_code == 200
        allocation_id = response.json()['data']['allocation']['allocation_id']

        # 4. Update the allocation
        updated_allocation_data = {
            "vehicle_id": vehicle_id,
            "from_datetime": (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
            "to_datetime": (datetime.now() + timedelta(days=2, hours=1)).isoformat(),
            "purpose": "Updated business trip"
        }

        response = await client.patch(f"/allocations/update/{allocation_id}", json=updated_allocation_data)
        assert response.status_code == 200
        assert response.json()['code'] == "VEHICLE_UPDATED"

        # 5. Get the allocation history for the unique employee
        response = await client.get(f"/allocations/history?employee_id={unique_employee_id}")
        assert response.status_code == 200
        allocations = response.json()['data']['allocations']
        assert len(allocations) > 0
        assert allocations[0]['employee_id'] == unique_employee_id
