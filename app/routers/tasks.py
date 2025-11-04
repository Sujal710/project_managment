# Import typing module to specify a list of items as type hints
from typing import List

# Import FastAPI components to create routes and handle dependencies/errors
from fastapi import APIRouter, Depends, HTTPException, status

# Import ObjectId from BSON (used to handle MongoDB’s unique document IDs)
from bson import ObjectId

# Import our data models (Task schema) and database class
from app.models import Task, TaskBase, TaskUpdate
from app.database import Database

# Create a router instance — this lets us group all routes related to "tasks"
router = APIRouter()


# ------------------- DEPENDENCIES -------------------

# This function retrieves a database connection from the main app
# It’s marked as async because FastAPI supports async DB operations
async def get_db():
    from main import get_database  # Import get_database function from main.py
    return get_database()  # Return the actual DB connection (like MongoDB client)


# This function provides a specialized database handler for the "tasks" collection
# It uses FastAPI's Depends to automatically inject the database connection
async def get_task_db(db = Depends(get_db)):
    # Create a Database instance targeting the "tasks" collection and Task model
    return Database(db, "tasks", Task)


# ------------------- CREATE TASK -------------------

@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskBase, db: Database = Depends(get_task_db)):
    """
    Create a new task in the database.
    """
    try:
        # Call the create() method from our Database class to insert new task data
        new_task = await db.create(task)

        # Return the created task document (FastAPI will automatically convert it to JSON)
        return new_task

    except Exception as e:
        # If anything goes wrong, return a 500 Internal Server Error with details
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )


# ------------------- GET ALL TASKS -------------------

@router.get("/", response_model=List[Task])
async def get_all_tasks(db: Database = Depends(get_task_db), skip: int = 0, limit: int = 100):
    """
    Retrieve a list of all tasks, with pagination support.
    """
    # Fetch all task documents from the collection (skip/limit for pagination)
    tasks = await db.get_all(skip=skip, limit=limit)
    return tasks  # Return the list of task objects


# ------------------- GET SINGLE TASK BY ID -------------------

@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str, db: Database = Depends(get_task_db)):
    """
    Retrieve a single task using its unique ID.
    """
    # Fetch a single task by its ID
    task = await db.get_by_id(task_id)

    # If no such task exists, raise a 404 error
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Return the found task
    return task


# ------------------- UPDATE TASK -------------------

@router.put("/{task_id}", response_model=Task)
async def update_task(task_id: str, task_update: TaskUpdate, db: Database = Depends(get_task_db)):
    """
    Update an existing task with new data.
    """
    # Try to update the task document with new field values
    updated_task = await db.update(task_id, task_update)

    # If no task was updated (ID invalid or no changes made), raise 404
    if updated_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or no changes made"
        )

    # Return the updated task document
    return updated_task


# ------------------- DELETE TASK -------------------

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, db: Database = Depends(get_task_db)):
    """
    Delete a specific task by ID.
    """
    # Try deleting the task
    deleted = await db.delete(task_id)

    # If deletion failed (e.g., invalid ID), raise an error
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Return nothing (204 = successful deletion, no content)
    return


# ------------------- GET TASK TIME SUMMARY -------------------

@router.get("/{task_id}/time-summary", response_model=dict)
async def get_task_time_summary(task_id: str, db: Database = Depends(get_task_db)):
    """
    Calculate total hours spent vs estimated hours for a given task.
    """

    # Validate that the provided task_id is a valid MongoDB ObjectId
    if not ObjectId.is_valid(task_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Task ID format"
        )
    
    # Fetch the specific task by its ID
    task = await db.get_by_id(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Import get_database from main (for direct access to 'time_logs' collection)
    from main import get_database
    time_logs_collection = get_database()["time_logs"]  # Select the time_logs collection
    
    # Create an aggregation pipeline to sum total hours spent per task
    pipeline = [
        {"$match": {"task_id": ObjectId(task_id)}},  # Match logs for this task
        {"$group": {  # Group them to sum total hours
            "_id": None,  # We don’t need to group by any field
            "total_hours_spent": {"$sum": "$hours_spent"},  # Add all hours
            "log_count": {"$sum": 1}  # Count total logs
        }}
    ]
    
    # Execute the aggregation query and convert the result to a list
    result = await time_logs_collection.aggregate(pipeline).to_list(length=1)
    
    # Extract the total hours spent and log count from result (or default to 0)
    total_hours_spent = result[0]['total_hours_spent'] if result else 0
    log_count = result[0]['log_count'] if result else 0
    
    # Get estimated hours from the task itself
    estimated_hours = task.estimated_duration_hours

    # Calculate difference between actual and estimated time
    difference = total_hours_spent - estimated_hours

    # Calculate what percentage of the estimate has been used
    percentage = (total_hours_spent / estimated_hours * 100) if estimated_hours > 0 else 0
    
    # Return all summary data in a dictionary
    return {
        "task_id": task_id,
        "task_name": task.name,
        "estimated_hours": estimated_hours,
        "total_hours_spent": total_hours_spent,
        "difference": difference,
        "percentage_used": round(percentage, 1),
        "time_logs_count": log_count,
        # Status depends on whether more or less time was spent than planned
        "status": (
            "over_budget" if difference > 0 
            else "under_budget" if difference < 0 
            else "on_budget"
        )
    }
