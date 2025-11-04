# ==============================
# 📂 File: app/routers/time_logs.py
# Description: Handles all API routes related to Time Logs (Create, Read, Update, Delete)
# ==============================

# Import List type to specify a list of response models
from typing import List

# Import FastAPI components
from fastapi import APIRouter, Depends, HTTPException, status

# Import our data models related to Time Logs
# TimeLog → represents a full time log entry (used in database)
# TimeLogBase → represents input data when creating a new log
# TimeLogUpdate → represents input data when updating a log
from app.models import TimeLog, TimeLogBase, TimeLogUpdate

# Import Database helper to handle MongoDB operations
from app.database import Database

# Create a new router object that will group all /time_logs related routes
router = APIRouter()

# -------------------------------
# 🧩 Dependency - Get database connection
# -------------------------------
async def get_db():
    # Import the database connection getter from main.py dynamically
    from main import get_database
    # Return a database instance (MongoDB client)
    return get_database()

# -------------------------------
# 🧩 Dependency - Get time_logs collection handler
# -------------------------------
async def get_timelog_db(db = Depends(get_db)):
    # Create a Database object for "time_logs" collection using TimeLog model
    return Database(db, "time_logs", TimeLog)

# -------------------------------
# 🧾 Create a new Time Log
# -------------------------------
@router.post("/", response_model=TimeLog, status_code=status.HTTP_201_CREATED)
async def create_time_log(time_log: TimeLogBase, db: Database = Depends(get_timelog_db)):
    """
    Create a new time log entry in the database.
    Example: recording that a member worked 3 hours on a task.
    """
    try:
        # Insert the new time log into the MongoDB "time_logs" collection
        new_log = await db.create(time_log)
        # Return the created log as a response
        return new_log
    except Exception as e:
        # If something goes wrong (e.g., database error), raise HTTP 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )

# -------------------------------
# 📋 Get all Time Logs
# -------------------------------
@router.get("/", response_model=List[TimeLog])
async def get_all_time_logs(
    db: Database = Depends(get_timelog_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Fetch all time logs from the database.
    Supports pagination using 'skip' and 'limit'.
    Example: GET /time_logs?skip=0&limit=10
    """
    # Fetch logs with pagination
    logs = await db.get_all(skip=skip, limit=limit)
    # Return the list of logs
    return logs

# -------------------------------
# 🔍 Get a single Time Log by ID
# -------------------------------
@router.get("/{log_id}", response_model=TimeLog)
async def get_time_log(log_id: str, db: Database = Depends(get_timelog_db)):
    """
    Retrieve one time log entry using its unique ID.
    Example: GET /time_logs/654b2d1ab3f12
    """
    # Try to find the time log in the database
    log = await db.get_by_id(log_id)
    # If log doesn't exist, raise a 404 error
    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time Log not found"
        )
    # Return the found log
    return log

# -------------------------------
# ✏️ Update a Time Log
# -------------------------------
@router.put("/{log_id}", response_model=TimeLog)
async def update_time_log(log_id: str, log_update: TimeLogUpdate, db: Database = Depends(get_timelog_db)):
    """
    Update an existing time log's details.
    Example: changing hours_spent from 3 to 4.
    """
    # Update the record in the database
    updated_log = await db.update(log_id, log_update)
    # If nothing was updated (log not found or no changes made)
    if updated_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time Log not found or no changes made"
        )
    # Return the updated log
    return updated_log

# -------------------------------
# 🗑️ Delete a Time Log
# -------------------------------
@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_time_log(log_id: str, db: Database = Depends(get_timelog_db)):
    """
    Delete a time log entry from the database by ID.
    Example: DELETE /time_logs/654b2d1ab3f12
    """
    # Attempt to delete the log
    deleted = await db.delete(log_id)
    # If deletion failed (log not found)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time Log not found"
        )
    # If successful, return 204 No Content (nothing to return)
    return
