# C:\Users\Sujal\Downloads\Project Management Assistant Functional Features Overview\app\routers\members.py

# Import required modules
from typing import List                         # Used to specify that some functions return a list
from fastapi import APIRouter, Depends, HTTPException, status  # FastAPI tools for routing, dependency injection, and error handling

# Import the models used for Member operations
from app.models import Member, MemberBase, MemberUpdate         # Data models for member creation, reading, and updating
from app.database import Database                              # Database helper class to interact with MongoDB

# Create a router instance for all endpoints related to members
router = APIRouter()


# -----------------------------
# DATABASE DEPENDENCY FUNCTIONS
# -----------------------------

# A helper function to import and return the active database connection from the main.py file
async def get_db():
    from main import get_database            # Import the get_database function dynamically to avoid circular imports
    return get_database()                    # Return the database instance


# Dependency to create a Database handler for the "members" collection
async def get_member_db(db = Depends(get_db)):  # Depends automatically injects the result of get_db()
    return Database(db, "members", Member)      # Create a Database object targeting the "members" collection


# -----------------------------
# ROUTES FOR MEMBER OPERATIONS
# -----------------------------

# 1️⃣ CREATE a new team member
@router.post("/", response_model=Member, status_code=status.HTTP_201_CREATED)
async def create_member(member: MemberBase, db: Database = Depends(get_member_db)):
    """
    Add a new team member to the database.
    """
    try:
        new_member = await db.create(member)     # Use the Database helper to insert a new member document
        return new_member                        # Return the created member data
    except Exception as e:
        # If something goes wrong (like DB connection or schema issue), raise a 500 Internal Server Error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )


# 2️⃣ GET all members (with optional pagination)
@router.get("/", response_model=List[Member])
async def get_all_members(db: Database = Depends(get_member_db), skip: int = 0, limit: int = 100):
    """
    Retrieve a list of all team members.
    - skip: how many records to skip (for pagination)
    - limit: how many records to return (max 100)
    """
    members = await db.get_all(skip=skip, limit=limit)   # Fetch members from database
    return members                                       # Return list of Member objects


# 3️⃣ GET a specific member by ID
@router.get("/{member_id}", response_model=Member)
async def get_member(member_id: str, db: Database = Depends(get_member_db)):
    """
    Retrieve a single team member by their unique ID.
    """
    member = await db.get_by_id(member_id)               # Fetch a single member using ID
    if member is None:                                   # If no member found, raise an error
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    return member                                        # Return the found member


# 4️⃣ UPDATE a member's profile
@router.put("/{member_id}", response_model=Member)
async def update_member(member_id: str, member_update: MemberUpdate, db: Database = Depends(get_member_db)):
    """
    Update an existing team member's profile (like name, skills, or availability).
    """
    updated_member = await db.update(member_id, member_update)   # Call update on DB with new data
    if updated_member is None:                                   # If member doesn't exist or no change made
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found or no changes made"
        )
    return updated_member                                        # Return the updated member details


# 5️⃣ DELETE a member by ID
@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(member_id: str, db: Database = Depends(get_member_db)):
    """
    Delete a team member using their ID.
    """
    deleted = await db.delete(member_id)                         # Try to delete member from DB
    if not deleted:                                              # If member does not exist
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    return                                                       # Return empty response (204 means success with no content)
