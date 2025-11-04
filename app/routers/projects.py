# C:\Users\Sujal\Downloads\Project Management Assistant Functional Features Overview\app\routers\projects.py

# -----------------------------
# IMPORTING REQUIRED MODULES
# -----------------------------
from typing import List                             # Used to define list type hints
from fastapi import APIRouter, Depends, HTTPException, status  # Tools from FastAPI to create routes and handle errors

# Import project-related models and the database helper
from app.models import Project, ProjectBase, ProjectUpdate      # Data models used for project operations
from app.database import Database                              # Helper class to interact with MongoDB database

# -----------------------------
# ROUTER INITIALIZATION
# -----------------------------
router = APIRouter()    # Create a new API router for all "project" endpoints


# -----------------------------
# DATABASE DEPENDENCIES
# -----------------------------

# Function to get the active database connection from main.py
async def get_db():
    from main import get_database       # Dynamically import the database function (prevents circular import issues)
    return get_database()               # Return the database instance to use in routes


# Create a database handler for the "projects" collection
async def get_project_db(db = Depends(get_db)):   # Depends automatically runs get_db() first
    # Create and return a Database object for "projects" collection using the Project model
    return Database(db, "projects", Project)


# -----------------------------
# API ROUTES FOR PROJECTS
# -----------------------------

# 1️⃣ CREATE a new project
@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectBase, db: Database = Depends(get_project_db)):
    """
    Create a new project entry in the database.
    """
    try:
        # Use our database helper to insert the new project document into MongoDB
        new_project = await db.create(project)
        return new_project                # Return the newly created project as the response
    except Exception as e:
        # If there’s any database error, return a 500 Internal Server Error with the error message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )


# 2️⃣ GET all projects (optionally with pagination)
@router.get("/", response_model=List[Project])
async def get_all_projects(db: Database = Depends(get_project_db), skip: int = 0, limit: int = 100):
    """
    Retrieve all projects from the database.
    You can use 'skip' and 'limit' to paginate results.
    Example: skip=0, limit=10 returns first 10 projects.
    """
    # Fetch all projects from the database, skipping and limiting results for pagination
    projects = await db.get_all(skip=skip, limit=limit)
    return projects                       # Return list of all project documents


# 3️⃣ GET a single project by ID
@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str, db: Database = Depends(get_project_db)):
    """
    Retrieve a single project using its unique project ID.
    """
    # Try to find the project in the database by its ID
    project = await db.get_by_id(project_id)
    if project is None:
        # If no project found with given ID, return 404 error
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project                        # Return the found project as response


# 4️⃣ UPDATE an existing project
@router.put("/{project_id}", response_model=Project)
async def update_project(project_id: str, project_update: ProjectUpdate, db: Database = Depends(get_project_db)):
    """
    Update the details of an existing project.
    Example: change its status, name, or deadlines.
    """
    # Update the project document in the database with new data
    updated_project = await db.update(project_id, project_update)
    if updated_project is None:
        # If project not found or no update performed, send a 404 error
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or no changes made"
        )
    return updated_project                # Return the updated project data


# 5️⃣ DELETE a project by ID
@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, db: Database = Depends(get_project_db)):
    """
    Delete a project permanently from the database using its ID.
    """
    # Try to delete the project document from MongoDB
    deleted = await db.delete(project_id)
    if not deleted:
        # If project not found, raise a 404 error
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return    # Return nothing (HTTP 204 means success, no content returned)
