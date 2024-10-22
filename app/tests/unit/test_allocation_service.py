import pytest
from unittest.mock import AsyncMock, MagicMock
from app.core.exceptions import DuplicateBookingError, VehicleUnavailableError
from app.core.services import AllocationService
from app.core.models import Allocation, Vehicle
from motor.motor_asyncio import AsyncIOMotorClient  # Mock the MongoDB client
from datetime import datetime


@pytest.mark.asyncio
async def test_allocate_vehicle_success(mocker):
    # Mock the repository, cache, and db_client using AsyncMock directly
    mock_allocation_repo = AsyncMock()
    mock_vehicle_repo = AsyncMock()
    mock_cache = AsyncMock()

    # Create a mock session and mock the async context manager behavior
    mock_session = MagicMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    # Mock the db_client and make start_session return an async context manager
    mock_db_client = AsyncMock(AsyncIOMotorClient)
    mock_db_client.start_session.return_value = mock_session

    # Set async return values for repository methods
    mock_vehicle_repo.get_vehicle_by_id.return_value = Vehicle(
        vehicle_id="v1",
        status="available",
        fuel_efficiency=15.5,
        make="Toyota",
        model="Corolla",
        capacity=4,
    )
    mock_allocation_repo.get_allocation_by_employee_and_date.return_value = (
        None  # No existing booking
    )
    mock_cache.get.return_value = None  # No cache for the employee or vehicle

    # Create the service with the mock db_client
    service = AllocationService(
        mock_allocation_repo, mock_vehicle_repo, mock_cache, mock_db_client
    )

    # Call the service method
    allocation = await service.allocate_vehicle(
        employee_id="emp1",
        vehicle_id="v1",
        from_datetime="2024-10-25T09:00:00",
        to_datetime="2024-10-25T18:00:00",
        purpose="Business Trip",
    )

    # Use dot notation to access the fields of allocation
    assert allocation.employee_id == "emp1"
    assert allocation.vehicle_id == "v1"
    assert mock_vehicle_repo.update_vehicle.called  # Ensure vehicle status was updated
    assert mock_allocation_repo.save_allocation.called  # Ensure allocation was saved
    assert mock_cache.set.called  # Ensure cache was updated


@pytest.mark.asyncio
async def test_allocate_vehicle_duplicate_booking(mocker):
    # Mock the repository, cache, and db_client using AsyncMock directly
    mock_allocation_repo = AsyncMock()
    mock_vehicle_repo = AsyncMock()
    mock_cache = AsyncMock()
    mock_db_client = AsyncMock(AsyncIOMotorClient)  # Mock db_client

    # Setup existing booking
    mock_allocation_repo.get_allocation_by_employee_and_date.return_value = {
        "employee_id": "emp1",
        "vehicle_id": "v1",
        "from_datetime": "2024-10-25T09:00:00",
        "to_datetime": "2024-10-25T18:00:00",
        "purpose": "Business Trip",
    }

    # Create the service
    service = AllocationService(
        mock_allocation_repo, mock_vehicle_repo, mock_cache, mock_db_client
    )

    # Assert custom DuplicateBookingError
    with pytest.raises(DuplicateBookingError):
        await service.allocate_vehicle(
            employee_id="emp1",
            vehicle_id="v2",
            from_datetime="2024-10-25T09:00:00",
            to_datetime="2024-10-25T18:00:00",
            purpose="Client Meeting",
        )

    assert not mock_vehicle_repo.update_vehicle.called


@pytest.mark.asyncio
async def test_allocate_vehicle_unavailable(mocker):
    # Mock the repository, cache, and db_client using AsyncMock directly
    mock_allocation_repo = AsyncMock()
    mock_vehicle_repo = AsyncMock()
    mock_cache = AsyncMock()
    mock_db_client = AsyncMock(AsyncIOMotorClient)  # Mock db_client

    # Ensure no existing booking for the employee
    mock_allocation_repo.get_allocation_by_employee_and_date.return_value = (
        None  # No existing booking for employee
    )

    # Mock vehicle is already allocated
    mock_vehicle_repo.get_vehicle_by_id.return_value = Vehicle(
        vehicle_id="v1",
        status="allocated",  # Vehicle is not available
        fuel_efficiency=15.5,
        make="Toyota",
        model="Corolla",
        capacity=4,
    )
    mock_cache.get.return_value = None  # Cache doesn't show the vehicle is allocated (to simulate fresh availability check)

    # Create the service
    service = AllocationService(
        mock_allocation_repo, mock_vehicle_repo, mock_cache, mock_db_client
    )

    # Now assert the custom exception VehicleUnavailableError
    with pytest.raises(VehicleUnavailableError):
        await service.allocate_vehicle(
            employee_id="emp1",
            vehicle_id="v1",
            from_datetime="2024-10-25T09:00:00",
            to_datetime="2024-10-25T18:00:00",
            purpose="Business Trip",
        )

    # Ensure the vehicle wasn't updated since it's unavailable
    assert not mock_vehicle_repo.update_vehicle.called


@pytest.mark.asyncio
async def test_update_allocation_success(mocker):
    # Mock the repository, cache, and db_client using AsyncMock directly
    mock_allocation_repo = AsyncMock()
    mock_vehicle_repo = AsyncMock()
    mock_cache = AsyncMock()

    # Create a mock session and mock the async context manager behavior
    mock_session = MagicMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    # Mock the db_client and make start_session return an async context manager
    mock_db_client = AsyncMock(AsyncIOMotorClient)
    mock_db_client.start_session.return_value = mock_session

    # Return a dictionary (not an Allocation object)
    mock_allocation_repo.get_allocation_by_id.return_value = {
        "allocation_id": "a1",
        "employee_id": "emp1",
        "vehicle_id": "v1",
        "from_datetime": "2024-10-25T09:00:00",
        "to_datetime": "2024-10-25T18:00:00",
        "status": "pending",
        "purpose": "Business Trip",
    }

    # Create the service
    service = AllocationService(
        mock_allocation_repo, mock_vehicle_repo, mock_cache, mock_db_client
    )

    # Update the allocation
    updated_allocation = await service.update_allocation(
        allocation_id="a1", from_datetime="2024-10-25T08:00:00"
    )

    # Assertions
    assert updated_allocation.from_datetime == "2024-10-25T08:00:00"  # Use dot notation
    assert (
        mock_allocation_repo.update_allocation.called
    )  # Ensure the allocation was updated
    assert mock_cache.delete.called  # Ensure cache was invalidated


@pytest.mark.asyncio
async def test_update_allocation_failure_after_approval(mocker):
    # Mock the repository, cache, and db_client using AsyncMock directly
    mock_allocation_repo = AsyncMock()
    mock_vehicle_repo = AsyncMock()
    mock_cache = AsyncMock()

    # Create a mock session and mock the async context manager behavior
    mock_session = MagicMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    # Mock the db_client and make start_session return an async context manager
    mock_db_client = AsyncMock(AsyncIOMotorClient)
    mock_db_client.start_session.return_value = mock_session

    # Returning a dictionary instead of an Allocation object
    mock_allocation_repo.get_allocation_by_id.return_value = {
        "allocation_id": "a1",
        "employee_id": "emp1",
        "vehicle_id": "v1",
        "from_datetime": "2024-10-25T09:00:00",
        "to_datetime": "2024-10-25T18:00:00",
        "status": "approved",
        "purpose": "Business Trip",
    }

    # Create the service
    service = AllocationService(
        mock_allocation_repo, mock_vehicle_repo, mock_cache, mock_db_client
    )

    # Attempt to update an approved allocation
    with pytest.raises(
        ValueError, match="Allocation is already approved and cannot be modified."
    ):
        await service.update_allocation(
            allocation_id="a1", from_datetime="2024-10-25T08:00:00"
        )

    # Ensure the allocation wasn't updated
    assert not mock_allocation_repo.update_allocation.called
