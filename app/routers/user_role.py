from fastapi import APIRouter

# Create a router instance
router = APIRouter()

# Define endpoints related to user roles
@router.get("/whoami")
async def get_user_role(role: str = "employee"):
    return {"role": role}
