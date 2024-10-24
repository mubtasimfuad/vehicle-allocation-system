
## Vehicle Allocation System - FastAPI Application

### Project Overview

This FastAPI-based system manages vehicle allocation for employees. It allows for creating, updating, and viewing allocation history. The project is containerized using Docker, features MongoDB and integrates Redis for caching.

### Features
- **CRUD Operations** for employee vehicle allocation.
- **History Report** with filtering and pagination.
- **MongoDB** for database operations
- **Redis Cache** to enhance performance.
- **Logging** for error and activity tracking.
- **Environment-driven Configurations** for database flexibility.
- **Dockerized** for seamless development and deployment.

### Project Structure

```bash
.
├── app
│   ├── core
│   │   ├── events.py        # Event handlers
│   │   ├── exceptions.py    # Custom exceptions
│   │   ├── models.py        # Data models (Allocation, Employee, Vehicle)
│   │   └── services.py      # Business logic for allocation
│   ├── events               # Event handling for message queue
│   │   ├── consumer.py
│   │   └── publisher.py
│   ├── infrastructure
│   │   ├── aws.py           # AWS-related integrations
│   │   ├── cache.py         # Redis caching setup
│   │   ├── config.py        # Configuration management
│   │   └── db.py            # MongoDB client setup
│   ├── routers              # API routes
│   │   ├── allocation.py    # Vehicle allocation endpoints
│   │   ├── report.py        # Report generation endpoints
│   │   └── user_role.py     # User role management
│   ├── tests                # Unit and integration tests
├── deploy_dev.yml           # Development environment deployment
├── docker-compose.yml       # Multi-container setup for production
├── Dockerfile               # Application container setup
├── logging.conf             # Logging configuration
├── main.py                  # Entry point for the application
├── mongo-init.js            # MongoDB initialization script
├── seed_data.py             # Seed data for MongoDB
├── utils.py                 # Utility functions
└── logs
    ├── app.log              # Application logs
    └── error.log            # Error logs
```

### Setup Instructions

1. **Prerequisites**
   - Ensure that Docker and Docker Compose are installed.

2. **Environment Variables**
   The application uses environment variables for configuration. Example:
   ```bash
   MONGO_DB_NAME=vehicle_allocation_db
   MONGO_URI=mongodb://mongo:27017/${MONGO_DB_NAME}?replicaSet=rs0
   REDIS_HOST=redis://redis:6379
   ```

3. **Build and Run the Application**
   To build and start the services, run:
   ```bash
   docker-compose up --build
   ```

4. **Database Initialization**
   The MongoDB instance is initialized with a replica set and seeded with data:
   - MongoDB: `mongo-init.js` initializes the replica set and seeds initial employee and vehicle data.
   - The MongoDB database name is dynamically set via environment variables.

5. **Access the Application**
   - The API will be available at `http://localhost:8000`.
   - API documentation: `http://localhost:8000/docs`.

6. **Logs**
   Application logs are stored in the `logs/` directory, mounted from the container.

### Running Tests
Unit tests can be executed using `pytest`:
```bash
pytest
```

### MongoDB Replica Set
The MongoDB container is configured to run a single-node replica set. The replica set is initialized by the `mongo-init.js` script,

### Deployment
- **Docker Compose** is used for both development and production environments.
- MongoDB and Redis are automatically set up in the containers.

### Conclusion
This project provides a dynamic, scalable vehicle allocation system ready for deployment with MongoDB's replica set and Redis caching.

---
