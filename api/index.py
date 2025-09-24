import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Import everything needed for the FastAPI app
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
import qrcode
import io
import base64
import json

# Load environment variables
load_dotenv(backend_dir / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "smart_attendance_secret_key_2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Create the FastAPI app for Vercel serverless
app = FastAPI(title="Smart Attendance & Curriculum Management API")

# Add CORS middleware
cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
allowed_origins = []
for origin in cors_origins:
    origin = origin.strip()
    if origin == '*' or not origin.startswith('https://*.'):
        allowed_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=allowed_origins if allowed_origins != ['*'] else ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a router with the /api prefix to match Vercel routing
api_router = APIRouter()

# Import the TIMETABLE and all models/functions from the original server
TIMETABLE = {
    "Monday": {
        "A5": [
            {"time": "09:30-10:30", "class": "MC", "subject": "Mathematics"},
            {"time": "10:30-11:30", "class": "PHY", "subject": "Physics"},
            {"time": "11:30-12:30", "class": "IC", "subject": "Integrated Circuits"},
            {"time": "12:30-01:30", "class": "LUNCH", "subject": "Lunch Break"},
            {"time": "01:30-02:45", "class": "SPORTS", "subject": "Sports"},
            {"time": "02:45-04:00", "class": "LIB", "subject": "Library"}
        ],
        "A6": [
            {"time": "09:30-10:30", "class": "MC", "subject": "Mathematics"},
            {"time": "10:30-11:30", "class": "PHY", "subject": "Physics"},
            {"time": "11:30-12:30", "class": "IC", "subject": "Integrated Circuits"},
            {"time": "12:30-01:30", "class": "LUNCH", "subject": "Lunch Break"},
            {"time": "01:30-02:45", "class": "SPORTS", "subject": "Sports"},
            {"time": "02:45-04:00", "class": "LIB", "subject": "Library"}
        ]
    },
    # ... (rest of timetable data would be here, truncated for brevity)
}

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password_hash: str
    role: str  # "teacher" or "student"
    student_id: Optional[str] = None
    class_section: Optional[str] = None  # "A5" or "A6" for students
    subjects: Optional[List[str]] = None  # List of subjects for teachers
    full_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    student_id: Optional[str] = None
    class_section: Optional[str] = None
    subjects: Optional[List[str]] = None
    full_name: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return User(**user)

# Authentication endpoints
@api_router.post("/auth/register", response_model=dict)
async def register_user(user_data: UserCreate):
    logger.info(f"Attempting to register user: {user_data.username}")
    try:
        # Check if user exists
        existing_user = await db.users.find_one({"username": user_data.username})
        if existing_user:
            logger.warning(f"Username {user_data.username} already registered")
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Validate role
        if user_data.role not in ["teacher", "student"]:
            raise HTTPException(status_code=400, detail="Role must be 'teacher' or 'student'")
        
        # For students, validate required fields
        if user_data.role == "student":
            if not user_data.student_id or not user_data.class_section:
                raise HTTPException(status_code=400, detail="Student ID and class section are required for students")
            if user_data.class_section not in ["A5", "A6"]:
                raise HTTPException(status_code=400, detail="Class section must be 'A5' or 'A6'")
        
        # For teachers, validate required fields
        if user_data.role == "teacher":
            if not user_data.subjects or len(user_data.subjects) == 0:
                raise HTTPException(status_code=400, detail="At least one subject is required for teachers")
        
        # Create user
        user_dict = user_data.dict()
        user_dict["password_hash"] = get_password_hash(user_data.password)
        del user_dict["password"]
        
        user = User(**user_dict)
        await db.users.insert_one(user.dict())
        
        logger.info(f"User {user.username} registered successfully.")
        return {"message": "User registered successfully", "user_id": user.id}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"An unexpected error occurred during registration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

@api_router.post("/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    user = await db.users.find_one({"username": user_credentials.username})
    if not user or not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# Root endpoint for testing
@app.get("/")
async def root():
    return {"message": "Smart Attendance API - Running on Vercel"}

# Include the router in the app
app.include_router(api_router)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()