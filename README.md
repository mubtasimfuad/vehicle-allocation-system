
## Vehicle Allocation System - FastAPI Application

### Description
This project implements a vehicle allocation system for company employees using **FastAPI** and **MongoDB**. Employees can allocate vehicles for a day, provided the vehicle is available. Features include allocation creation, updating, deletion, and a history report with filters. The system is optimized for high performance with caching and includes a dynamic MongoDB database.

### Features
- **CRUD** operations for vehicle allocation.
- **History report** with filters for employees and vehicles.
- MongoDB **Replica Set** configuration for data resilience.
- **Caching** with Redis to optimize performance.
- **Containerized** using Docker for easy deployment.
- **Unit tests** and **Swagger** documentation for APIs.

### Project Structure
```bash
.
├── app
│   ├── main.py          # Entry point
│   ├── models.py        # Models for Employee, Vehicle, Allocation
│   ├── db.py            # MongoDB and Redis connection
│   ├── routes.py        # API endpoints
│   ├── services.py      # Core allocation business logic
│   ├── utils.py         # Utility functions (e.g., caching)
├── Dockerfile           # Docker configuration for app
├── docker-compose.yml   # Multi-service Docker config
├── seed_data.py         # Script for inserting seed data
├── logging.conf         # Logging configuration
├── mongo-init.js        # MongoDB replica initialization script
├── Pipfile              # Pipenv dependency management
└── README.md            # Project documentation
```

### Prerequisites
- **Docker** and **Docker Compose** installed.
- Clone this repository.

### Setup

1. **Environment Variables**:
   - You can modify `MONGO_DB_NAME` and `MONGO_URI` in `docker-compose.yml` for your database.
   - Redis and MongoDB are integrated dynamically with environmental variables.

2. **Build and Run**:
   ```bash
   docker-compose up --build
   ```

3. **Access the API**:
   - The application will be available at `http://localhost:8000`.
   - API documentation is available at `http://localhost:8000/docs`.

4. **Testing**:
   Run unit tests with:
   ```bash
   pytest
   ```

### MongoDB Replica Set
A single-node MongoDB replica set is configured within `docker-compose.yml`. The initialization script (`mongo-init.js`) ensures the replica set is established, and seed data is inserted upon start.

### Deployment
This system can be deployed via Docker on any cloud platform supporting containerized applications (e.g., AWS ECS, GCP, Azure). MongoDB and Redis configurations are dynamically adjustable, ensuring flexibility in cloud environments.

