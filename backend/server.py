from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
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
from fastapi.responses import JSONResponse

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
    except:
        # Default to 1 hour from now if parsing fails
        return datetime.now(timezone.utc) + timedelta(hours=1)

# Authentication endpoints
@api_router.post("/auth/register", response_model=dict)
async def register_user(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
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
    
    return {"message": "User registered successfully", "user_id": user.id}

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

# QR Session endpoints
@api_router.post("/qr/generate")
async def generate_qr_session(qr_data: QRSessionCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can generate QR codes")
    
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
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can view QR sessions")
    
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
    elif current_user.role == "teacher":
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
    else:
        # Return full timetable for teachers
        return TIMETABLE

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()