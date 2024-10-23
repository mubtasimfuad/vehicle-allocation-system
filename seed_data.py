import os
from pymongo import MongoClient
from uuid import uuid4
from datetime import datetime, timedelta

# Get MongoDB connection details from environment variables
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv(
    "MONGO_DB_NAME", "vehicle_allocation_db"
)  # Use dynamic database name

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# Drop existing collections for clean seeding (optional, depends on your use case)
db.users.drop()
db.vehicles.drop()
db.allocations.drop()

# Seed Employees
employees = [
    {
        "employee_id": str(uuid4()),
        "name": "Abdul Rahman",
        "email": "abdul.rahman@example.com",
        "role": "EMPLOYEE",
    },
    {
        "employee_id": str(uuid4()),
        "name": "Fatima Khatun",
        "email": "fatima.khatun@example.com",
        "role": "DRIVER",
    },
    {
        "employee_id": str(uuid4()),
        "name": "Sultan Ahmed",
        "email": "sultan.ahmed@example.com",
        "role": "ADMIN",
    },
    {
        "employee_id": str(uuid4()),
        "name": "Nurul Islam",
        "email": "nurul.islam@example.com",
        "role": "EMPLOYEE",
    },
    {
        "employee_id": str(uuid4()),
        "name": "Shirin Akter",
        "email": "shirin.akter@example.com",
        "role": "DRIVER",
    },
]
db.users.insert_many(employees)

# Seed Vehicles (Common in Bangladesh)
vehicles = [
    {
        "vehicle_id": str(uuid4()),
        "make": "Toyota",
        "model": "Corolla",
        "status": "available",
    },
    {
        "vehicle_id": str(uuid4()),
        "make": "Honda",
        "model": "Civic",
        "status": "in_maintenance",
    },
    {
        "vehicle_id": str(uuid4()),
        "make": "Mitsubishi",
        "model": "Pajero",
        "status": "available",
    },
    {
        "vehicle_id": str(uuid4()),
        "make": "Nissan",
        "model": "Sunny",
        "status": "booked",
    },
    {
        "vehicle_id": str(uuid4()),
        "make": "Hyundai",
        "model": "Tucson",
        "status": "available",
    },
]
db.vehicles.insert_many(vehicles)

# Seed Allocations
allocations = [
    {
        "allocation_id": str(uuid4()),
        "employee_id": employees[0]["employee_id"],  # Abdul Rahman
        "vehicle_id": vehicles[0]["vehicle_id"],  # Toyota Corolla
        "from_datetime": datetime.now() + timedelta(days=1),
        "to_datetime": datetime.now() + timedelta(days=2),
        "purpose": "Business trip to Dhaka",
        "status": "approved",
    },
    {
        "allocation_id": str(uuid4()),
        "employee_id": employees[1]["employee_id"],  # Fatima Khatun (Driver)
        "vehicle_id": vehicles[2]["vehicle_id"],  # Mitsubishi Pajero
        "from_datetime": datetime.now() + timedelta(days=3),
        "to_datetime": datetime.now() + timedelta(days=5),
        "purpose": "Delivery of goods to Chittagong",
        "status": "pending",
    },
    {
        "allocation_id": str(uuid4()),
        "employee_id": employees[3]["employee_id"],  # Nurul Islam
        "vehicle_id": vehicles[4]["vehicle_id"],  # Hyundai Tucson
        "from_datetime": datetime.now() + timedelta(days=4),
        "to_datetime": datetime.now() + timedelta(days=6),
        "purpose": "Site visit to Rajshahi",
        "status": "approved",
    },
]
db.allocations.insert_many(allocations)

print(
    f"Database '{MONGO_DB_NAME}' seeded successfully with users, vehicles, and allocations."
)
