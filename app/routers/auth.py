# app/routers/auth.py

# =============================
# 📦 IMPORTS
# =============================
from datetime import datetime, timedelta        # To handle current time and token expiry
from typing import Optional                     # For declaring optional parameters in functions
from fastapi import APIRouter, Depends, HTTPException, status   # FastAPI classes for routing and errors
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # For Bearer Token Auth
from pydantic import BaseModel, EmailStr, field_validator        # For defining data models and validations
import bcrypt                                    # Used to securely hash passwords
from jose import JWTError, jwt                   # To create and decode JWT tokens
from bson import ObjectId                        # For working with MongoDB Object IDs

from app.database import Database                # Our custom Database helper class
from app.models import MongoBaseModel            # Base model that supports MongoDB fields

# =============================
# 🔧 BASIC CONFIGURATION
# =============================
router = APIRouter()                             # Create FastAPI router for auth routes
security = HTTPBearer()                          # Define Bearer Token authentication method

# Secret key and JWT configuration
SECRET_KEY = "your-secret-key-change-this-in-production"   # Used to sign JWT tokens
ALGORITHM = "HS256"                                       # Encryption algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24                     # Tokens last for 24 hours

# =============================
# 👤 USER MODELS
# =============================
class User(MongoBaseModel):                    # Model representing a user in MongoDB
    email: EmailStr                            # User's email (validated automatically)
    username: str                              # Unique username
    hashed_password: str                       # Hashed password (never store plain password)
    full_name: str                             # Full name
    is_active: bool = True                     # Status flag to disable user if needed
    created_at: datetime = datetime.utcnow()   # Timestamp when user is created

# Model used when creating a new user (before hashing password)
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str

    # Validate password length before accepting
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v):
        if len(v.encode('utf-8')) > 72:                # bcrypt can't hash >72 bytes
            raise ValueError('Password is too long. Maximum length is 72 bytes.')
        if len(v) < 6:                                 # Ensure password is not too short
            raise ValueError('Password must be at least 6 characters long.')
        return v                                       # Return valid password

# Model for login credentials
class UserLogin(BaseModel):
    username: str
    password: str

# Model for token response
class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict                                       # Contains username, email, etc.

# Model for data extracted from JWT token
class TokenData(BaseModel):
    username: Optional[str] = None

# =============================
# 🗄️ DATABASE DEPENDENCIES
# =============================
async def get_db():
    """Get database connection from main.py"""
    from main import get_database
    return get_database()                            # Return active database instance

async def get_user_db(db = Depends(get_db)):
    """Return user collection handler"""
    return Database(db, "users", User)               # Connect to 'users' collection

# =============================
# 🔐 PASSWORD UTILITIES
# =============================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare entered password with stored hashed password"""
    password_bytes = plain_password.encode('utf-8')       # Convert string to bytes
    if len(password_bytes) > 72:                          # Truncate if too long
        password_bytes = password_bytes[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))  # Compare both

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    password_bytes = password.encode('utf-8')             # Convert to bytes
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()                               # Generate random salt
    hashed = bcrypt.hashpw(password_bytes, salt)           # Create hashed password
    return hashed.decode('utf-8')                         # Convert bytes to string

# =============================
# 🔑 JWT TOKEN FUNCTIONS
# =============================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Generate JWT token for a user"""
    to_encode = data.copy()                                # Copy user data (e.g. {"sub": username})
    if expires_delta:                                      # If custom expiry provided
        expire = datetime.utcnow() + expires_delta
    else:                                                  # Default 15 minutes expiry
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})                      # Add expiry field to payload
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # Create token
    return encoded_jwt

# =============================
# 👤 CURRENT USER RETRIEVAL
# =============================
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),  # Extract token from header
    db: Database = Depends(get_user_db)
):
    """Decode token and return the currently logged-in user"""
    # If token invalid, raise this error
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials                             # Extract actual token string
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # Decode JWT
        username: str = payload.get("sub")                          # Extract username from token
        if username is None:                                        # If missing, invalid token
            raise credentials_exception
        token_data = TokenData(username=username)                   # Store username inside TokenData
    except JWTError:                                                # If decoding fails
        raise credentials_exception
    
    # Find user by username in DB
    cursor = db.collection.find({"username": token_data.username})
    users = await cursor.to_list(length=1)
    if not users:                                                   # If no match found
        raise credentials_exception
    
    user = User.model_validate(users[0])                            # Convert Mongo doc → User model
    if not user.is_active:                                          # Check if user is active
        raise HTTPException(status_code=400, detail="Inactive user")
    return user                                                     # Return user object if valid

# =============================
# 🚀 ROUTES
# =============================

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Database = Depends(get_user_db)):
    """Register a new user"""
    print(f"Registration attempt - Username: {user_data.username}, Email: {user_data.email}")
    
    # Check for existing username
    existing_user = await db.collection.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    # Check for existing email
    existing_email = await db.collection.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Hash password and create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name
    )
    
    # Save user to MongoDB
    user_dict = user.model_dump(by_alias=True, exclude_none=True, exclude={'id'})   # Convert to dict
    result = await db.collection.insert_one(user_dict)
    
    # Create token for this new user
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    
    print(f"User registered successfully: {user.username}")
    
    # Return token + user info
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    }

# =============================
# 🔓 LOGIN ROUTE
# =============================
@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Database = Depends(get_user_db)):
    """Authenticate user and return access token"""
    
    # Search user in DB
    user_doc = await db.collection.find_one({"username": user_data.username})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Convert to User model
    user = User.model_validate(user_doc)
    
    # Verify password using bcrypt
    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    
    # Return token + user details
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    }

# =============================
# 👤 GET CURRENT USER DETAILS
# =============================
@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Return info of logged-in user"""
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name
    }
