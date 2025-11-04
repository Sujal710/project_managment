# ===========================================================
# main.py — Entry point for the Project Management Assistant API
# ===========================================================

# Importing necessary modules
import os  # Used to access environment variables from the system or .env file
from contextlib import asynccontextmanager  # Helps manage startup and shutdown operations asynchronously

# FastAPI and related imports
from fastapi import FastAPI  # Main FastAPI class used to create the app
from fastapi.middleware.cors import CORSMiddleware  # Middleware to handle CORS (Cross-Origin Resource Sharing)

# MongoDB (async) and environment variable handling
from motor.motor_asyncio import AsyncIOMotorClient  # Async client for MongoDB (Motor library)
from dotenv import load_dotenv  # Loads environment variables from a .env file

# ===========================================================
# Load environment variables
# ===========================================================

load_dotenv()  # Reads the .env file in the project directory and loads variables into environment

# ===========================================================
# Configuration settings
# ===========================================================

# Get MongoDB connection string and database name from .env
# If not found, use default values
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "pm_assistant_db")

# ===========================================================
# Global variables for database connection
# ===========================================================

# These will hold the MongoDB client and database instance after connecting
db_client: AsyncIOMotorClient = None
database = None

# ===========================================================
# Lifespan function — handles app startup and shutdown events
# ===========================================================

@asynccontextmanager  # This decorator allows async setup and teardown for FastAPI
async def lifespan(app: FastAPI):
    """
    Context manager that runs on application startup and shutdown.
    Used here to connect to and close MongoDB.
    """
    global db_client, database  # Declare globals so we can modify them

    print("Connecting to MongoDB...")  # Log to console (useful for debugging)

    try:
        # Create MongoDB async client
        db_client = AsyncIOMotorClient(MONGO_URI)

        # Ping MongoDB to verify connection
        await db_client.admin.command("ping")

        # Access specific database
        database = db_client[DATABASE_NAME]

        print("✅ Successfully connected to MongoDB.")
    except Exception as e:
        # Handle failed connection attempt
        print(f"❌ Could not connect to MongoDB: {e}")
        db_client = None
        database = None

    # Yield control back to FastAPI while app is running
    yield

    # ===========================================================
    # Code below runs when the app is shutting down
    # ===========================================================
    if db_client:
        print("Closing MongoDB connection...")
        db_client.close()  # Properly close MongoDB connection
        print("✅ MongoDB connection closed.")

# ===========================================================
# Initialize FastAPI app
# ===========================================================

app = FastAPI(
    title="Project Management Assistant API",  # API title (shown in docs)
    description="A backend API for a Project Management Assistant built with FastAPI and MongoDB.",  # Description for docs
    version="1.0.0",  # Version number
    lifespan=lifespan  # Register our startup/shutdown manager
)

# ===========================================================
# Enable CORS Middleware
# ===========================================================

# This allows frontend apps (like React, Angular, etc.) to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (good for development, restrict in production)
    allow_credentials=True,  # Allow cookies or authentication headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all custom headers
)

# ===========================================================
# Root endpoint
# ===========================================================

@app.get("/")  # Define a GET route at the root URL (http://localhost:8000/)
async def root():
    """Root endpoint — useful for a quick health check."""
    return {"message": "Project Management Assistant API is running!"}

# ===========================================================
# Importing all routers (modular route files)
# ===========================================================

# Each router handles a specific module of the app
from app.routers import (
    projects,  # Handles project-related CRUD operations
    tasks,     # Handles tasks under each project
    members,   # Manages team members data
    time_logs, # Manages time tracking entries
    assignment,# Manages task/project assignments
    auth       # Handles authentication (login, signup, etc.)
)

# ===========================================================
# Register routers with FastAPI app
# ===========================================================

# Add all routers to the main FastAPI app with URL prefixes and tags
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(members.router, prefix="/members", tags=["Members"])
app.include_router(time_logs.router, prefix="/time_logs", tags=["Time Logs"])
app.include_router(assignment.router, prefix="/assignment", tags=["Assignment System"])

# ===========================================================
# Database dependency
# ===========================================================

def get_database():
    """
    Returns the MongoDB database instance.
    Used as a dependency in routers to access collections.
    """
    if database is None:
        # If the connection failed or hasn't been established, raise an error
        raise ConnectionError("Database connection is not established.")
    return database  # Return the connected database instance

# ===========================================================
# End of file
# ===========================================================
