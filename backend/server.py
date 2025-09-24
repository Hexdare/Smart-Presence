from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
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

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

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

# Create the main app without a prefix
app = FastAPI(title="Smart Attendance & Curriculum Management API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Timetable data
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
    "Tuesday": {
        "A5": [
            {"time": "09:30-10:30", "class": "PHY", "subject": "Physics"},
            {"time": "10:30-11:30", "class": "CAD LAB", "subject": "CAD Lab"},
            {"time": "11:30-12:30", "class": "CAD LAB", "subject": "CAD Lab"},
            {"time": "12:30-01:30", "class": "LUNCH", "subject": "Lunch Break"},
            {"time": "01:30-02:45", "class": "MC", "subject": "Mathematics"},
            {"time": "02:45-04:00", "class": "MC(T)", "subject": "Mathematics (Tutorial)"}
        ],
        "A6": [
            {"time": "09:30-10:30", "class": "PHY", "subject": "Physics"},
            {"time": "10:30-11:30", "class": "COMM LAB", "subject": "Communication Lab"},
            {"time": "11:30-12:30", "class": "COMM LAB", "subject": "Communication Lab"},
            {"time": "12:30-01:30", "class": "LUNCH", "subject": "Lunch Break"},
            {"time": "01:30-02:45", "class": "MC", "subject": "Mathematics"},
            {"time": "02:45-04:00", "class": "MC (T)", "subject": "Mathematics (Tutorial)"}
        ]
    },
    "Wednesday": {
        "A5": [
            {"time": "09:30-10:30", "class": "ENG", "subject": "English"},
            {"time": "10:30-11:30", "class": "PHY LAB", "subject": "Physics Lab"},
            {"time": "11:30-12:30", "class": "PHY LAB", "subject": "Physics Lab"},
            {"time": "12:30-01:30", "class": "LUNCH", "subject": "Lunch Break"},
            {"time": "01:30-02:45", "class": "MC", "subject": "Mathematics"},
            {"time": "02:45-04:00", "class": "PME", "subject": "Production and Manufacturing Engineering"}
        ],
        "A6": [
            {"time": "09:30-10:30", "class": "ENG", "subject": "English"},
            {"time": "10:30-11:30", "class": "BEE LAB", "subject": "Basic Electrical Engineering Lab"},
            {"time": "11:30-12:30", "class": "BEE LAB", "subject": "Basic Electrical Engineering Lab"},
            {"time": "12:30-01:30", "class": "LUNCH", "subject": "Lunch Break"},
            {"time": "01:30-02:45", "class": "MC", "subject": "Mathematics"},
            {"time": "02:45-04:00", "class": "PME", "subject": "Production and Manufacturing Engineering"}
        ]
    },
    "Thursday": {
        "A5": [
            {"time": "09:30-10:30", "class": "PHY", "subject": "Physics"},
            {"time": "10:30-11:30", "class": "BEE LAB", "subject": "Basic Electrical Engineering Lab"},
            {"time": "11:30-12:30", "class": "BEE LAB", "subject": "Basic Electrical Engineering Lab"},
            {"time": "12:30-01:30", "class": "LUNCH", "subject": "Lunch Break"},
            {"time": "01:30-02:45", "class": "MC", "subject": "Mathematics"},
            {"time": "02:45-04:00", "class": "BEE", "subject": "Basic Electrical Engineering"}
        ],
        "A6": [
            {"time": "09:30-10:30", "class": "PHY", "subject": "Physics"},
            {"time": "10:30-11:30", "class": "PHY LAB", "subject": "Physics Lab"},
            {"time": "11:30-12:30", "class": "PHY LAB", "subject": "Physics Lab"},
            {"time": "12:30-01:30", "class": "LUNCH", "subject": "Lunch Break"},
            {"time": "01:30-02:45", "class": "MC", "subject": "Mathematics"},
            {"time": "02:45-04:00", "class": "BEE", "subject": "Basic Electrical Engineering"}
        ]
    },
    "Friday": {
        "A5": [
            {"time": "09:30-10:30", "class": "BEE", "subject": "Basic Electrical Engineering"},
            {"time": "10:30-11:30", "class": "COMM LAB", "subject": "Communication Lab"},
            {"time": "11:30-12:30", "class": "COMM LAB", "subject": "Communication Lab"},
            {"time": "12:30-01:30", "class": "LUNCH", "subject": "Lunch Break"},
            {"time": "01:30-02:45", "class": "", "subject": ""},
            {"time": "02:20-04:00", "class": "IC", "subject": "Integrated Circuits"}
        ],
        "A6": [
            {"time": "09:30-10:30", "class": "BEE", "subject": "Basic Electrical Engineering"},
            {"time": "10:30-11:30", "class": "CAD LAB", "subject": "CAD Lab"},
            {"time": "11:30-12:30", "class": "CAD LAB", "subject": "CAD Lab"},
            {"time": "12:30-01:30", "class": "LUNCH", "subject": "Lunch Break"},
            {"time": "01:30-02:45", "class": "NAMAZ", "subject": "Prayer Break"},
            {"time": "02:20-04:00", "class": "IC", "subject": "Integrated Circuits"}
        ]
    },
    "Saturday": {
        "A5": [
            {"time": "09:30-10:30", "class": "MC", "subject": "Mathematics"},
            {"time": "10:30-11:30", "class": "BEE", "subject": "Basic Electrical Engineering"},
            {"time": "11:30-12:30", "class": "ENG", "subject": "English"},
            {"time": "12:30-01:30", "class": "LUNCH", "subject": "Lunch Break"},
            {"time": "01:30-02:45", "class": "ECA", "subject": "Extra Curricular Activities"},
            {"time": "02:45-04:00", "class": "ECA", "subject": "Extra Curricular Activities"}
        ],
        "A6": [
            {"time": "09:30-10:30", "class": "MC", "subject": "Mathematics"},
            {"time": "10:30-11:30", "class": "BEE", "subject": "Basic Electrical Engineering"},
            {"time": "11:30-12:30", "class": "ENG", "subject": "English"},
            {"time": "12:30-01:30", "class": "LUNCH", "subject": "Lunch Break"},
            {"time": "01:30-02:45", "class": "ECA", "subject": "Extra Curricular Activities"},
            {"time": "02:45-04:00", "class": "ECA", "subject": "Extra Curricular Activities"}
        ]
    }
}

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password_hash: str
    role: str  # "teacher", "student", or "principal"
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

class QRSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    teacher_id: str
    teacher_name: str
    class_section: str
    subject: str
    class_code: str
    time_slot: str
    qr_data: str
    qr_image: str  # base64 encoded QR image
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    is_active: bool = True

class QRSessionCreate(BaseModel):
    class_section: str
    subject: str
    class_code: str
    time_slot: str

class AttendanceRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    student_name: str
    qr_session_id: str
    class_section: str
    subject: str
    class_code: str
    time_slot: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AttendanceCreate(BaseModel):
    qr_data: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Announcement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    author_id: str
    author_name: str
    author_role: str  # "teacher", "principal"
    target_audience: str  # "all", "teachers", "students", "A5", "A6"
    image_url: Optional[str] = None
    image_data: Optional[str] = None  # base64 encoded image
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class AnnouncementCreate(BaseModel):
    title: str
    content: str
    target_audience: str = "all"
    image_data: Optional[str] = None  # base64 encoded image

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    target_audience: Optional[str] = None
    image_data: Optional[str] = None
    is_active: Optional[bool] = None

class EmergencyAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    student_name: str
    class_section: str
    alert_type: str  # "fire", "unauthorized_access", "other"
    description: Optional[str] = None  # For "other" type alerts
    status: str = "pending"  # "pending", "acknowledged", "resolved"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None  # Principal user ID who resolved it
    resolver_name: Optional[str] = None  # Principal name who resolved it

class EmergencyAlertCreate(BaseModel):
    alert_type: str
    description: Optional[str] = None

class EmergencyAlertStatusUpdate(BaseModel):
    status: str  # "acknowledged", "resolved"

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

def generate_qr_code(data: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode()

def parse_time_slot(time_slot: str):
    """Parse time slot like '09:30-10:30' to get end time"""
    try:
        start_time, end_time = time_slot.split('-')
        end_hour, end_minute = map(int, end_time.split(':'))
        
        now = datetime.now(timezone.utc)
        # Assuming same day for simplicity
        expire_time = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
        
        # If the end time has passed for today, set for tomorrow
        if expire_time <= now:
            expire_time += timedelta(days=1)
        
        return expire_time
    except Exception:
        # Default to 1 hour from now if parsing fails
        return datetime.now(timezone.utc) + timedelta(hours=1)

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
        if user_data.role not in ["teacher", "student", "principal"]:
            raise HTTPException(status_code=400, detail="Role must be 'teacher', 'student', or 'principal'")
        
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
        
        # For principals, validate required fields (principals can teach subjects but it's optional)
        if user_data.role == "principal":
            # Principals have all permissions, no specific validation needed
            pass
        
        # Create user
        user_dict = user_data.dict()
        user_dict["password_hash"] = get_password_hash(user_data.password)
        del user_dict["password"]
        
        user = User(**user_dict)
        await db.users.insert_one(user.dict())
        
        logger.info(f"User {user.username} registered successfully.")
        return {"message": "User registered successfully", "user_id": user.id}
    except HTTPException as e:
        # Re-raise HTTPExceptions to let FastAPI handle them
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

# Helper function to get current active classes for a teacher
def get_current_active_classes(teacher_subjects: List[str]):
    """Get currently active classes based on current time and teacher's subjects"""
    now = datetime.now(timezone.utc)
    current_time = now.strftime("%H:%M")
    current_day = now.strftime("%A")
    
    active_classes = []
    
    if current_day in TIMETABLE:
        for section_name, periods in TIMETABLE[current_day].items():
            for period in periods:
                # Check if this period matches teacher's subjects
                subject_match = False
                for teacher_subject in teacher_subjects:
                    if (teacher_subject.lower() in period["subject"].lower() or 
                        period["subject"].lower() in teacher_subject.lower() or
                        period["class"] == teacher_subject):
                        subject_match = True
                        break
                
                if subject_match:
                    # Parse time slot to check if class is currently active
                    time_parts = period["time"].split('-')
                    if len(time_parts) == 2:
                        start_time = time_parts[0].strip()
                        end_time = time_parts[1].strip()
                        
                        # Convert to comparable format (remove colons for simple comparison)
                        current_minutes = int(current_time.replace(":", ""))
                        start_minutes = int(start_time.replace(":", ""))
                        end_minutes = int(end_time.replace(":", ""))
                        
                        # Check if current time is within class period
                        if start_minutes <= current_minutes <= end_minutes:
                            class_info = period.copy()
                            class_info["section"] = section_name
                            class_info["day"] = current_day
                            active_classes.append(class_info)
    
    return active_classes

# New endpoint to get current active classes
@api_router.get("/qr/active-classes")
async def get_active_classes(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["teacher", "principal"]:
        raise HTTPException(status_code=403, detail="Only teachers and principals can view active classes")
    
    if not current_user.subjects:
        return {"active_classes": [], "message": "No subjects assigned"}
    
    active_classes = get_current_active_classes(current_user.subjects)
    return {"active_classes": active_classes, "current_time": datetime.now(timezone.utc).isoformat()}

# Enhanced QR generation for active classes
@api_router.post("/qr/generate-for-active-class")
async def generate_qr_for_active_class(class_info: dict, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["teacher", "principal"]:
        raise HTTPException(status_code=403, detail="Only teachers and principals can generate QR codes")
    
    # Verify this is actually an active class for this teacher
    active_classes = get_current_active_classes(current_user.subjects or [])
    
    # Find matching active class
    matching_class = None
    for active_class in active_classes:
        if (active_class["section"] == class_info.get("section") and 
            active_class["subject"] == class_info.get("subject") and
            active_class["time"] == class_info.get("time")):
            matching_class = active_class
            break
    
    if not matching_class:
        raise HTTPException(status_code=400, detail="No active class found for the specified parameters")
    
    # Generate QR session
    qr_session_id = str(uuid.uuid4())
    qr_session_data = {
        "session_id": qr_session_id,
        "teacher_id": current_user.id,
        "class_section": matching_class["section"],
        "subject": matching_class["subject"],
        "time_slot": matching_class["time"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    qr_data_str = json.dumps(qr_session_data)
    qr_image = generate_qr_code(qr_data_str)
    
    # Calculate exact expiry time based on class end time
    expires_at = parse_time_slot(matching_class["time"])
    
    # Create QR session
    qr_session = QRSession(
        id=qr_session_id,
        teacher_id=current_user.id,
        teacher_name=current_user.full_name,
        class_section=matching_class["section"],
        subject=matching_class["subject"],
        class_code=matching_class["class"],
        time_slot=matching_class["time"],
        qr_data=qr_data_str,
        qr_image=qr_image,
        expires_at=expires_at
    )
    
    await db.qr_sessions.insert_one(qr_session.dict())
    
    return {
        "session_id": qr_session_id,
        "qr_image": qr_image,
        "qr_data": qr_data_str,
        "expires_at": expires_at.isoformat(),
        "class_section": matching_class["section"],
        "subject": matching_class["subject"],
        "time_slot": matching_class["time"],
        "class_code": matching_class["class"]
    }

# Keep the original QR generation as backup/manual option
@api_router.post("/qr/generate")
async def generate_qr_session(qr_data: QRSessionCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["teacher", "principal"]:
        raise HTTPException(status_code=403, detail="Only teachers and principals can generate QR codes")
    
    # Validate that teacher can teach this subject
    if current_user.subjects:
        subject_match = False
        for teacher_subject in current_user.subjects:
            if (teacher_subject.lower() in qr_data.subject.lower() or 
                qr_data.subject.lower() in teacher_subject.lower()):
                subject_match = True
                break
        
        if not subject_match:
            raise HTTPException(status_code=403, detail="You are not authorized to create QR codes for this subject")
    
    # Validate class section
    if qr_data.class_section not in ["A5", "A6"]:
        raise HTTPException(status_code=400, detail="Class section must be 'A5' or 'A6'")
    
    # Generate QR data
    qr_session_id = str(uuid.uuid4())
    qr_session_data = {
        "session_id": qr_session_id,
        "teacher_id": current_user.id,
        "class_section": qr_data.class_section,
        "subject": qr_data.subject,
        "time_slot": qr_data.time_slot,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    qr_data_str = json.dumps(qr_session_data)
    qr_image = generate_qr_code(qr_data_str)
    
    # Calculate expiry time based on time slot
    expires_at = parse_time_slot(qr_data.time_slot)
    
    # Create QR session
    qr_session = QRSession(
        id=qr_session_id,
        teacher_id=current_user.id,
        teacher_name=current_user.full_name,
        class_section=qr_data.class_section,
        subject=qr_data.subject,
        class_code=qr_data.class_code,
        time_slot=qr_data.time_slot,
        qr_data=qr_data_str,
        qr_image=qr_image,
        expires_at=expires_at
    )
    
    await db.qr_sessions.insert_one(qr_session.dict())
    
    return {
        "session_id": qr_session_id,
        "qr_image": qr_image,
        "qr_data": qr_data_str,
        "expires_at": expires_at.isoformat(),
        "class_section": qr_data.class_section,
        "subject": qr_data.subject,
        "time_slot": qr_data.time_slot
    }

@api_router.get("/qr/sessions")
async def get_teacher_qr_sessions(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["teacher", "principal"]:
        raise HTTPException(status_code=403, detail="Only teachers and principals can view QR sessions")
    
    sessions = await db.qr_sessions.find({"teacher_id": current_user.id}).to_list(100)
    return [QRSession(**session) for session in sessions]

# Attendance endpoints
@api_router.post("/attendance/mark")
async def mark_attendance(attendance_data: AttendanceCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can mark attendance")
    
    try:
        # Parse QR data
        qr_info = json.loads(attendance_data.qr_data)
        session_id = qr_info["session_id"]
        
        # Find QR session
        qr_session = await db.qr_sessions.find_one({"id": session_id})
        if not qr_session:
            raise HTTPException(status_code=404, detail="Invalid QR code")
        
        # Check if session is still active and not expired
        expires_at = qr_session["expires_at"]
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        elif expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if not qr_session["is_active"] or datetime.now(timezone.utc) > expires_at:
            raise HTTPException(status_code=400, detail="QR code has expired")
        
        # Check if student belongs to the correct class section
        if current_user.class_section != qr_session["class_section"]:
            raise HTTPException(status_code=400, detail="You are not enrolled in this class section")
        
        # Check if already marked attendance
        existing_attendance = await db.attendance.find_one({
            "student_id": current_user.student_id,
            "qr_session_id": session_id
        })
        if existing_attendance:
            raise HTTPException(status_code=400, detail="Attendance already marked for this session")
        
        # Create attendance record
        attendance = AttendanceRecord(
            student_id=current_user.student_id,
            student_name=current_user.full_name,
            qr_session_id=session_id,
            class_section=qr_session["class_section"],
            subject=qr_session["subject"],
            class_code=qr_session["class_code"],
            time_slot=qr_session["time_slot"]
        )
        
        await db.attendance.insert_one(attendance.dict())
        
        return {"message": "Attendance marked successfully", "attendance_id": attendance.id}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid QR code format")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/attendance/records")
async def get_attendance_records(current_user: User = Depends(get_current_user)):
    if current_user.role == "student":
        # Students see their own attendance
        records = await db.attendance.find({"student_id": current_user.student_id}).to_list(1000)
    elif current_user.role in ["teacher", "principal"]:
        if current_user.role == "principal":
            # Principals see all attendance records
            records = await db.attendance.find({}).to_list(1000)
        else:
            # Teachers see attendance for their sessions
            qr_sessions = await db.qr_sessions.find({"teacher_id": current_user.id}).to_list(1000)
            session_ids = [session["id"] for session in qr_sessions]
            records = await db.attendance.find({"qr_session_id": {"$in": session_ids}}).to_list(1000)
    else:
        records = []
    
    return [AttendanceRecord(**record) for record in records]

@api_router.get("/timetable")
async def get_timetable(current_user: User = Depends(get_current_user)):
    if current_user.role == "student" and current_user.class_section:
        # Return timetable for student's class section
        student_timetable = {}
        for day, sections in TIMETABLE.items():
            if current_user.class_section in sections:
                student_timetable[day] = sections[current_user.class_section]
        return student_timetable
    elif current_user.role in ["teacher", "principal"]:
        if current_user.role == "principal":
            # Principals see the full timetable
            return TIMETABLE
        elif current_user.subjects:
            # Return filtered timetable for teacher's subjects
            teacher_timetable = {}
            teacher_subjects = current_user.subjects
            
            for day, sections in TIMETABLE.items():
                day_classes = []
                # Check both A5 and A6 sections for teacher's subjects
                for section_name, periods in sections.items():
                    for period in periods:
                        # Match subjects (case-insensitive and partial match)
                        subject_match = False
                        for teacher_subject in teacher_subjects:
                            if (teacher_subject.lower() in period["subject"].lower() or 
                                period["subject"].lower() in teacher_subject.lower() or
                                period["class"] == teacher_subject):
                                subject_match = True
                                break
                        
                        if subject_match:
                            # Add section info to the period
                            period_with_section = period.copy()
                            period_with_section["section"] = section_name
                            day_classes.append(period_with_section)
                
                if day_classes:
                    teacher_timetable[day] = day_classes
            
            return teacher_timetable
        else:
            return {}
    else:
        # Return full timetable as fallback
        return TIMETABLE

# Helper function to filter announcements based on user role and target audience
def filter_announcements_for_user(announcements, user_role, class_section=None):
    """Filter announcements based on target audience and user permissions"""
    filtered = []
    for announcement in announcements:
        target = announcement["target_audience"]
        if (target == "all" or 
            target == user_role or 
            (target == "students" and user_role == "student") or
            (target == "teachers" and user_role in ["teacher", "principal"]) or
            (target == class_section and class_section)):
            filtered.append(announcement)
    return filtered

# Announcements endpoints
@api_router.post("/announcements", response_model=dict)
async def create_announcement(announcement_data: AnnouncementCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["teacher", "principal"]:
        raise HTTPException(status_code=403, detail="Only teachers and principals can create announcements")
    
    # Validate target_audience
    valid_audiences = ["all", "students", "teachers", "A5", "A6"]
    if announcement_data.target_audience not in valid_audiences:
        raise HTTPException(status_code=400, detail=f"Target audience must be one of: {', '.join(valid_audiences)}")
    
    # Create announcement
    announcement = Announcement(
        title=announcement_data.title,
        content=announcement_data.content,
        author_id=current_user.id,
        author_name=current_user.full_name,
        author_role=current_user.role,
        target_audience=announcement_data.target_audience,
        image_data=announcement_data.image_data
    )
    
    await db.announcements.insert_one(announcement.dict())
    
    return {"message": "Announcement created successfully", "announcement_id": announcement.id}

@api_router.get("/announcements")
async def get_announcements(current_user: User = Depends(get_current_user)):
    try:
        # Get all active announcements
        announcements = await db.announcements.find({"is_active": True}).sort("created_at", -1).to_list(1000)
        
        # Filter based on user role and permissions
        filtered_announcements = filter_announcements_for_user(
            announcements, 
            current_user.role, 
            current_user.class_section
        )
        
        return [Announcement(**announcement) for announcement in filtered_announcements]
    except Exception as e:
        logger.error(f"Error fetching announcements: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch announcements")

@api_router.get("/announcements/{announcement_id}")
async def get_announcement(announcement_id: str, current_user: User = Depends(get_current_user)):
    announcement = await db.announcements.find_one({"id": announcement_id, "is_active": True})
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    # Check if user can view this announcement
    filtered = filter_announcements_for_user([announcement], current_user.role, current_user.class_section)
    if not filtered:
        raise HTTPException(status_code=403, detail="You don't have permission to view this announcement")
    
    return Announcement(**announcement)

@api_router.put("/announcements/{announcement_id}")
async def update_announcement(
    announcement_id: str, 
    update_data: AnnouncementUpdate, 
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["teacher", "principal"]:
        raise HTTPException(status_code=403, detail="Only teachers and principals can update announcements")
    
    # Find the announcement
    announcement = await db.announcements.find_one({"id": announcement_id})
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    # Check if user is the author or a principal
    if announcement["author_id"] != current_user.id and current_user.role != "principal":
        raise HTTPException(status_code=403, detail="You can only update your own announcements")
    
    # Prepare update data
    update_fields = {}
    if update_data.title is not None:
        update_fields["title"] = update_data.title
    if update_data.content is not None:
        update_fields["content"] = update_data.content
    if update_data.target_audience is not None:
        valid_audiences = ["all", "students", "teachers", "A5", "A6"]
        if update_data.target_audience not in valid_audiences:
            raise HTTPException(status_code=400, detail=f"Target audience must be one of: {', '.join(valid_audiences)}")
        update_fields["target_audience"] = update_data.target_audience
    if update_data.image_data is not None:
        update_fields["image_data"] = update_data.image_data
    if update_data.is_active is not None:
        update_fields["is_active"] = update_data.is_active
    
    if update_fields:
        update_fields["updated_at"] = datetime.now(timezone.utc)
        await db.announcements.update_one({"id": announcement_id}, {"$set": update_fields})
    
    return {"message": "Announcement updated successfully"}

@api_router.delete("/announcements/{announcement_id}")
async def delete_announcement(announcement_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["teacher", "principal"]:
        raise HTTPException(status_code=403, detail="Only teachers and principals can delete announcements")
    
    # Find the announcement
    announcement = await db.announcements.find_one({"id": announcement_id})
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    # Check if user is the author or a principal
    if announcement["author_id"] != current_user.id and current_user.role != "principal":
        raise HTTPException(status_code=403, detail="You can only delete your own announcements")
    
    # Soft delete by setting is_active to False
    await db.announcements.update_one(
        {"id": announcement_id}, 
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
    )
    
    return {"message": "Announcement deleted successfully"}

# Timetable management for principals
@api_router.put("/timetable")
async def update_timetable(timetable_data: dict, current_user: User = Depends(get_current_user)):
    if current_user.role != "principal":
        raise HTTPException(status_code=403, detail="Only principals can update the timetable")
    
    # Validate timetable structure (basic validation)
    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    valid_sections = ["A5", "A6"]
    
    for day, sections in timetable_data.items():
        if day not in valid_days:
            raise HTTPException(status_code=400, detail=f"Invalid day: {day}")
        
        if not isinstance(sections, dict):
            raise HTTPException(status_code=400, detail=f"Sections for {day} must be an object")
        
        for section, periods in sections.items():
            if section not in valid_sections:
                raise HTTPException(status_code=400, detail=f"Invalid section: {section}")
            
            if not isinstance(periods, list):
                raise HTTPException(status_code=400, detail=f"Periods for {day}-{section} must be an array")
    
    # Update the global timetable (in a real app, this would be stored in database)
    global TIMETABLE
    TIMETABLE.update(timetable_data)
    
    return {"message": "Timetable updated successfully"}

# Emergency Alert endpoints
@api_router.post("/emergency-alerts", response_model=dict)
async def create_emergency_alert(alert_data: EmergencyAlertCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can create emergency alerts")
    
    # Validate alert type
    valid_alert_types = ["fire", "unauthorized_access", "other"]
    if alert_data.alert_type not in valid_alert_types:
        raise HTTPException(status_code=400, detail=f"Alert type must be one of: {', '.join(valid_alert_types)}")
    
    # For "other" type, description is required
    if alert_data.alert_type == "other" and not alert_data.description:
        raise HTTPException(status_code=400, detail="Description is required for 'other' type alerts")
    
    # Create emergency alert
    emergency_alert = EmergencyAlert(
        student_id=current_user.student_id,
        student_name=current_user.full_name,
        class_section=current_user.class_section,
        alert_type=alert_data.alert_type,
        description=alert_data.description
    )
    
    await db.emergency_alerts.insert_one(emergency_alert.dict())
    
    return {"message": "Emergency alert created successfully", "alert_id": emergency_alert.id}

@api_router.get("/emergency-alerts")
async def get_emergency_alerts(current_user: User = Depends(get_current_user)):
    try:
        # All roles can view emergency alerts, but with different scopes
        if current_user.role == "student":
            # Students see their own alerts
            alerts = await db.emergency_alerts.find({"student_id": current_user.student_id}).sort("created_at", -1).to_list(1000)
        elif current_user.role in ["teacher", "principal"]:
            # Teachers and principals see all alerts
            alerts = await db.emergency_alerts.find({}).sort("created_at", -1).to_list(1000)
        else:
            alerts = []
        
        return [EmergencyAlert(**alert) for alert in alerts]
    except Exception as e:
        logger.error(f"Error fetching emergency alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch emergency alerts")

@api_router.put("/emergency-alerts/{alert_id}/status")
async def update_emergency_alert_status(
    alert_id: str, 
    status_update: EmergencyAlertStatusUpdate, 
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "principal":
        raise HTTPException(status_code=403, detail="Only principals can update emergency alert status")
    
    # Find the alert
    alert = await db.emergency_alerts.find_one({"id": alert_id})
    if not alert:
        raise HTTPException(status_code=404, detail="Emergency alert not found")
    
    # Validate status
    valid_statuses = ["acknowledged", "resolved"]
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(valid_statuses)}")
    
    # Prepare update data
    update_fields = {
        "status": status_update.status
    }
    
    current_time = datetime.now(timezone.utc)
    if status_update.status == "acknowledged":
        update_fields["acknowledged_at"] = current_time
    elif status_update.status == "resolved":
        update_fields["resolved_at"] = current_time
        update_fields["resolved_by"] = current_user.id
        update_fields["resolver_name"] = current_user.full_name
    
    await db.emergency_alerts.update_one({"id": alert_id}, {"$set": update_fields})
    
    return {"message": f"Emergency alert status updated to {status_update.status}"}

@api_router.get("/emergency-alerts/{alert_id}")
async def get_emergency_alert(alert_id: str, current_user: User = Depends(get_current_user)):
    alert = await db.emergency_alerts.find_one({"id": alert_id})
    if not alert:
        raise HTTPException(status_code=404, detail="Emergency alert not found")
    
    # Check permissions
    if current_user.role == "student" and alert["student_id"] != current_user.student_id:
        raise HTTPException(status_code=403, detail="You can only view your own alerts")
    elif current_user.role not in ["teacher", "principal", "student"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return EmergencyAlert(**alert)

# Add CORS middleware BEFORE including router
cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
# Handle wildcard patterns for Vercel deployment
allowed_origins = []
for origin in cors_origins:
    origin = origin.strip()
    if origin == '*' or not origin.startswith('https://*.'):
        allowed_origins.append(origin)
    else:
        # For patterns like https://*.vercel.app, we'll use allow_origin_regex
        continue

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=allowed_origins if allowed_origins != ['*'] else ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router in the main app
app.include_router(api_router)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
