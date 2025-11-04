# C:\Users\Sujal\Downloads\Project Management Assistant Functional Features Overview\app\routers\assignment.py

# Importing required modules
from typing import List                         # For type hinting, e.g., List[str]
from fastapi import APIRouter, Depends, HTTPException, status  # FastAPI tools for routing, dependencies, and error handling
from bson import ObjectId                        # Used to work with MongoDB ObjectId

# Importing models and database helper
from app.models import Task, Member              # Import Task and Member models (data structure of documents)
from app.database import Database                # Import custom Database helper class for MongoDB operations

# Create a new API router to define endpoints related to assignments or workloads
router = APIRouter()

# ----------------------------------------------------------
# 1️⃣ Dependency to get the main database connection
# ----------------------------------------------------------
async def get_db():
    # Import the database getter from main.py dynamically (to avoid circular imports)
    from main import get_database
    # Return the database connection (most likely a MongoDB instance)
    return get_database()

# ----------------------------------------------------------
# 2️⃣ Dependency for the "tasks" collection
# ----------------------------------------------------------
async def get_task_db(db = Depends(get_db)):
    # Create a Database object specifically for the "tasks" collection
    # It will use the Task model to structure its documents
    return Database(db, "tasks", Task)

# ----------------------------------------------------------
# 3️⃣ Dependency for the "members" collection
# ----------------------------------------------------------
async def get_member_db(db = Depends(get_db)):
    # Same as above but for the "members" collection using the Member model
    return Database(db, "members", Member)

# ----------------------------------------------------------
# 4️⃣ Define the endpoint to calculate a member’s workload
# ----------------------------------------------------------
@router.get("/workload/{member_id}", response_model=dict)
async def get_member_workload(
    member_id: str, 
    task_db: Database = Depends(get_task_db),     # Injects the "tasks" collection database helper
    member_db: Database = Depends(get_member_db)  # Injects the "members" collection database helper
):
    """
    Calculate the current workload for a specific team member.
    Workload = sum of estimated duration hours for all tasks assigned
    to the member that are NOT yet marked as 'Done'.
    """

    # ------------------------------------------------------
    # 5️⃣ Validate that the provided member_id is a valid MongoDB ObjectId
    # ------------------------------------------------------
    if not ObjectId.is_valid(member_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # Return a 400 (Bad Request) error
            detail="Invalid Member ID format"         # Inform client about the invalid ID
        )

    # ------------------------------------------------------
    # 6️⃣ Retrieve the member details from the database
    # ------------------------------------------------------
    member = await member_db.get_by_id(member_id)     # Get member record by ID
    if member is None:
        # If no such member exists, return a 404 (Not Found)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    # ------------------------------------------------------
    # 7️⃣ Build a MongoDB aggregation pipeline
    # ------------------------------------------------------
    # This pipeline finds all tasks assigned to this member
    # where the task status is NOT 'Done', then sums up the total hours
    # and counts the number of such tasks.
    pipeline = [
        {"$match": {                                # Step 1: Filter matching tasks
            "assigned_to_ids": ObjectId(member_id),  # Task must include this member ID
            "status": {"$ne": "Done"}                # Exclude tasks that are 'Done'
        }},
        {"$group": {                                # Step 2: Group and calculate totals
            "_id": None,                            # Group all results together
            "total_estimated_hours": {"$sum": "$estimated_duration_hours"},  # Sum up all estimated hours
            "active_tasks_count": {"$sum": 1}       # Count how many tasks matched
        }}
    ]

    # ------------------------------------------------------
    # 8️⃣ Execute the aggregation on the tasks collection
    # ------------------------------------------------------
    result = await task_db.collection.aggregate(pipeline).to_list(length=1)
    # Converts the aggregation result into a list (we only expect one item)

    # ------------------------------------------------------
    # 9️⃣ Extract values or default to 0 if no tasks were found
    # ------------------------------------------------------
    total_estimated_hours = result[0]['total_estimated_hours'] if result else 0
    active_tasks_count = result[0]['active_tasks_count'] if result else 0

    # ------------------------------------------------------
    # 🔟 Return a structured JSON response containing the workload info
    # ------------------------------------------------------
    return {
        "member_id": member_id,                                   # The ID of the member
        "member_name": member.name,                               # Member’s name from DB
        "availability_percent": member.availability_percent,       # How available the member is (from DB)
        "active_tasks_count": active_tasks_count,                 # Number of active (not Done) tasks
        "total_estimated_hours_assigned": total_estimated_hours,  # Sum of all estimated hours
        "note": "Workload is the sum of estimated hours for all non-Done tasks assigned to the member."
    }
