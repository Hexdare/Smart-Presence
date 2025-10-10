from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
import qrcode
import io
import base64
import json
import hashlib
import asyncio
import tempfile
import shutil
import csv
import re
# OCR and document processing imports
import pytesseract
import cv2
import numpy as np
from PIL import Image
import PyPDF2
import pdfplumber
import textdistance

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
    role: str  # "teacher", "student", "principal", "verifier", "institution_admin", "system_admin"
    student_id: Optional[str] = None
    class_section: Optional[str] = None  # "A5" or "A6" for students
    subjects: Optional[List[str]] = None  # List of subjects for teachers
    institution_id: Optional[str] = None  # For institution_admin role
    full_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    student_id: Optional[str] = None
    class_section: Optional[str] = None
    subjects: Optional[List[str]] = None
    institution_id: Optional[str] = None
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

# Certificate Verification Models
class Institution(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: str  # Unique institution code
    type: str  # "university", "college", "institute"
    state: str
    city: str
    established_year: int
    accreditation: Optional[str] = None
    contact_email: str
    contact_phone: str
    website: Optional[str] = None
    is_verified: bool = False
    verification_hash: str  # For hash-based verification
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InstitutionCreate(BaseModel):
    name: str
    code: str
    type: str
    state: str
    city: str
    established_year: int
    accreditation: Optional[str] = None
    contact_email: str
    contact_phone: str
    website: Optional[str] = None

class Certificate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    certificate_id: str  # Certificate number from institution
    student_name: str
    father_name: Optional[str] = None
    roll_number: str
    registration_number: str
    course_name: str
    course_type: str  # "degree", "diploma", "certificate"
    course_duration: str
    passing_year: int
    grade: str
    percentage: Optional[float] = None
    cgpa: Optional[float] = None
    institution_id: str
    institution_name: str
    issued_date: datetime
    certificate_hash: str  # Hash for verification
    metadata: dict = {}  # Additional certificate details
    is_verified: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CertificateCreate(BaseModel):
    certificate_id: str
    student_name: str
    father_name: Optional[str] = None
    roll_number: str
    registration_number: str
    course_name: str
    course_type: str
    course_duration: str
    passing_year: int
    grade: str
    percentage: Optional[float] = None
    cgpa: Optional[float] = None
    institution_id: str
    issued_date: datetime
    metadata: dict = {}

class VerificationRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    requester_id: str
    requester_name: str
    requester_organization: Optional[str] = None
    file_path: str
    file_type: str  # "pdf", "jpg", "png", etc.
    file_size: int
    ocr_text: Optional[str] = None
    extracted_data: dict = {}  # Structured data from OCR
    verification_status: str = "pending"  # "pending", "processing", "verified", "rejected", "failed"
    confidence_score: Optional[float] = None
    matched_certificate_id: Optional[str] = None
    anomalies_detected: List[str] = []
    verification_notes: Optional[str] = None
    processed_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None

class VerificationRequestCreate(BaseModel):
    requester_organization: Optional[str] = None

class VerificationResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    verification_request_id: str
    is_authentic: bool
    confidence_score: float
    matched_certificate: Optional[dict] = None
    anomalies: List[dict] = []
    verification_details: dict = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DocumentAnalysis(BaseModel):
    text_extracted: str
    confidence_score: float
    detected_fields: dict
    anomalies: List[str]
    processing_time: float

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

# OCR and Document Processing Functions
def preprocess_image(image_path: str) -> np.ndarray:
    """Preprocess image for better OCR results"""
    try:
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            # Try with PIL if cv2 fails
            pil_img = Image.open(image_path)
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh
    except Exception as e:
        logger.error(f"Image preprocessing failed: {str(e)}")
        return None

def extract_text_from_image(image_path: str) -> Dict[str, Any]:
    """Extract text from image using Tesseract OCR"""
    try:
        start_time = datetime.now()
        
        # Preprocess image
        processed_img = preprocess_image(image_path)
        
        if processed_img is None:
            # Fallback to direct OCR
            text = pytesseract.image_to_string(Image.open(image_path))
        else:
            # Use processed image
            text = pytesseract.image_to_string(processed_img)
        
        # Get confidence data
        data = pytesseract.image_to_data(Image.open(image_path), output_type=pytesseract.Output.DICT)
        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "text": text.strip(),
            "confidence": avg_confidence,
            "processing_time": processing_time,
            "method": "tesseract_ocr"
        }
    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}")
        return {
            "text": "",
            "confidence": 0,
            "processing_time": 0,
            "method": "tesseract_ocr",
            "error": str(e)
        }

def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """Extract text from PDF using PyPDF2 and pdfplumber"""
    try:
        start_time = datetime.now()
        text = ""
        metadata = {}
        
        # First try with pdfplumber (better for complex layouts)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata = {
                    "pages": len(pdf.pages),
                    "metadata": pdf.metadata or {}
                }
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.warning(f"pdfplumber failed, trying PyPDF2: {str(e)}")
            
            # Fallback to PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = {
                    "pages": len(pdf_reader.pages),
                    "metadata": pdf_reader.metadata or {}
                }
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "text": text.strip(),
            "confidence": 95.0,  # PDF text extraction is usually very reliable
            "processing_time": processing_time,
            "method": "pdf_extraction",
            "metadata": metadata
        }
    except Exception as e:
        logger.error(f"PDF processing failed: {str(e)}")
        return {
            "text": "",
            "confidence": 0,
            "processing_time": 0,
            "method": "pdf_extraction",
            "error": str(e)
        }

def extract_certificate_fields(text: str) -> Dict[str, Any]:
    """Extract structured data from certificate text using pattern matching"""
    import re
    
    fields = {}
    
    # Common certificate patterns
    patterns = {
        "name": [
            r"(?:name|student|candidate)[:.]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(?:mr|ms|miss)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(?:this is to certify that)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        ],
        "father_name": [
            r"(?:father|s/o|son of|daughter of)[:.]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(?:father's name)[:.]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        ],
        "roll_number": [
            r"(?:roll|roll no|enrollment|enroll)[:.]?\s*([A-Z0-9]+)",
            r"(?:student id|id no)[:.]?\s*([A-Z0-9]+)"
        ],
        "registration_number": [
            r"(?:registration|reg no|registration no)[:.]?\s*([A-Z0-9]+)",
        ],
        "course": [
            r"(?:course|degree|diploma|program)[:.]?\s*([A-Za-z\s&]+)",
            r"(?:bachelor|master|btech|be|mtech|me|bca|mca|bsc|msc)[\s\w]*",
        ],
        "year": [
            r"(?:year|passed|passing|completion)[:.]?\s*(\d{4})",
            r"(?:in the year|academic year)[:.]?\s*(\d{4})",
        ],
        "grade": [
            r"(?:grade|class|division)[:.]?\s*([A-Z\+\-]+)",
            r"(?:with|secured)[:.]?\s*([A-Z\+\-]+)\s*(?:grade|class)"
        ],
        "percentage": [
            r"(\d+\.?\d*)%",
            r"(?:percentage|marks)[:.]?\s*(\d+\.?\d*)"
        ],
        "cgpa": [
            r"(?:cgpa|gpa)[:.]?\s*(\d+\.?\d*)",
        ]
    }
    
    # Extract fields using patterns
    for field, field_patterns in patterns.items():
        for pattern in field_patterns:
            match = re.search(pattern, text.lower())
            if match:
                fields[field] = match.group(1).strip()
                break
    
    return fields

def detect_anomalies(text: str, extracted_fields: Dict[str, Any]) -> List[str]:
    """Detect potential anomalies in certificate text"""
    anomalies = []
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r"photoshop",
        r"edit",
        r"modified",
        r"fake",
        r"duplicate"
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, text.lower()):
            anomalies.append(f"Suspicious text detected: {pattern}")
    
    # Check for inconsistent formatting
    if text:
        # Check for unusual character patterns
        if len(re.findall(r'[^\w\s]', text)) > len(text) * 0.1:
            anomalies.append("Unusual character density detected")
        
        # Check for mixed fonts (approximate)
        if len(set(text)) / len(text) > 0.3:
            anomalies.append("Possible mixed font usage detected")
    
    # Validate extracted fields
    if "year" in extracted_fields:
        try:
            year = int(extracted_fields["year"])
            current_year = datetime.now().year
            if year > current_year or year < 1950:
                anomalies.append(f"Invalid graduation year: {year}")
        except ValueError:
            anomalies.append("Invalid year format")
    
    if "percentage" in extracted_fields:
        try:
            percentage = float(extracted_fields["percentage"])
            if percentage > 100 or percentage < 0:
                anomalies.append(f"Invalid percentage: {percentage}")
        except ValueError:
            anomalies.append("Invalid percentage format")
    
    return anomalies

def generate_certificate_hash(certificate_data: Dict[str, Any]) -> str:
    """Generate a hash for certificate verification"""
    # Create a canonical string representation
    keys = sorted(certificate_data.keys())
    canonical_string = ""
    
    for key in keys:
        if key in certificate_data and certificate_data[key] is not None:
            canonical_string += f"{key}:{str(certificate_data[key])}"
    
    # Generate SHA-256 hash
    hash_object = hashlib.sha256(canonical_string.encode())
    return hash_object.hexdigest()

async def process_document(file_path: str, file_type: str) -> DocumentAnalysis:
    """Main document processing function"""
    try:
        start_time = datetime.now()
        
        if file_type.lower() == 'pdf':
            extraction_result = extract_text_from_pdf(file_path)
        else:
            extraction_result = extract_text_from_image(file_path)
        
        if not extraction_result["text"]:
            return DocumentAnalysis(
                text_extracted="",
                confidence_score=0,
                detected_fields={},
                anomalies=["No text could be extracted from document"],
                processing_time=(datetime.now() - start_time).total_seconds()
            )
        
        # Extract structured fields
        fields = extract_certificate_fields(extraction_result["text"])
        
        # Detect anomalies
        anomalies = detect_anomalies(extraction_result["text"], fields)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return DocumentAnalysis(
            text_extracted=extraction_result["text"],
            confidence_score=extraction_result["confidence"],
            detected_fields=fields,
            anomalies=anomalies,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Document processing failed: {str(e)}")
        return DocumentAnalysis(
            text_extracted="",
            confidence_score=0,
            detected_fields={},
            anomalies=[f"Processing error: {str(e)}"],
            processing_time=0
        )

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
    
    # First check if it's system admin using environment variables
    try:
        import os
        
        # Get system admin credentials from environment variables
        system_admin_username = os.environ.get("SYSTEM_ADMIN_USERNAME")
        system_admin_full_name = os.environ.get("SYSTEM_ADMIN_FULL_NAME", "System Administrator")
        
        if system_admin_username and system_admin_username == username:
            # Return system admin user object
            return User(
                id=str(uuid.uuid4()),
                username=system_admin_username,
                password_hash="",  # Not needed for auth check
                role="system_admin",
                full_name=system_admin_full_name
            )
    except Exception as e:
        logger.error(f"System admin user check failed: {str(e)}")
    
    # Check regular users in database
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
        
        # Validate role (system_admin is not registerable - use pre-configured credentials)
        # Only verifier and institution_admin can register publicly
        # teacher, student, principal can only be created by system admin
        public_allowed_roles = ["verifier", "institution_admin"]
        if user_data.role not in public_allowed_roles:
            raise HTTPException(status_code=403, detail=f"Role '{user_data.role}' can only be created by system administrators. Allowed roles for public registration: {', '.join(public_allowed_roles)}")
        
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
        
        # For institution admins, validate institution_id is provided
        if user_data.role == "institution_admin":
            if not user_data.institution_id:
                raise HTTPException(status_code=400, detail="Institution ID is required for institution admins")
        
        # For verifiers, no additional validation required
        if user_data.role == "verifier":
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

@api_router.post("/admin/users/create", response_model=dict)
async def create_user_admin(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user)
):
    """Create user with any role (system_admin only)"""
    if current_user.role != "system_admin":
        raise HTTPException(status_code=403, detail="Only system administrators can create users with restricted roles")
    
    logger.info(f"System admin creating user: {user_data.username} with role: {user_data.role}")
    try:
        # Check if user exists
        existing_user = await db.users.find_one({"username": user_data.username})
        if existing_user:
            logger.warning(f"Username {user_data.username} already exists")
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Validate role - system admin can create any role except system_admin
        allowed_roles = ["teacher", "student", "principal", "verifier", "institution_admin"]
        if user_data.role not in allowed_roles:
            raise HTTPException(status_code=400, detail=f"Invalid role. Allowed roles: {', '.join(allowed_roles)}")
        
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
        
        # For institution admins, validate institution_id is provided
        if user_data.role == "institution_admin":
            if not user_data.institution_id:
                raise HTTPException(status_code=400, detail="Institution ID is required for institution admins")
            # Verify institution exists
            institution = await db.institutions.find_one({"id": user_data.institution_id})
            if not institution:
                raise HTTPException(status_code=400, detail="Institution not found")
        
        # For verifiers, no additional validation required
        if user_data.role == "verifier":
            pass
        
        # Hash password
        password_hash = get_password_hash(user_data.password)
        
        # Create user object
        new_user = User(
            username=user_data.username,
            password_hash=password_hash,
            role=user_data.role,
            student_id=user_data.student_id,
            class_section=user_data.class_section,
            subjects=user_data.subjects,
            institution_id=user_data.institution_id,
            full_name=user_data.full_name
        )
        
        # Insert into database
        result = await db.users.insert_one(new_user.dict())
        new_user.id = str(result.inserted_id)
        
        logger.info(f"User created successfully: {user_data.username} with role: {user_data.role}")
        return {
            "message": "User created successfully",
            "user_id": new_user.id,
            "username": new_user.username,
            "role": new_user.role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="User creation failed")

@api_router.get("/admin/users", response_model=dict)
async def list_users_admin(
    current_user: User = Depends(get_current_user)
):
    """List all users (system_admin only)"""
    if current_user.role != "system_admin":
        raise HTTPException(status_code=403, detail="Only system administrators can view all users")
    
    try:
        users = []
        async for user in db.users.find({}):
            users.append({
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "full_name": user["full_name"],
                "student_id": user.get("student_id"),
                "class_section": user.get("class_section"),
                "subjects": user.get("subjects", []),
                "institution_id": user.get("institution_id"),
                "created_at": user["created_at"]
            })
        
        return {"users": users}
        
    except Exception as e:
        logger.error(f"User listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="User listing failed")

@api_router.post("/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    # First check if it's system admin login using environment variables
    try:
        import os
        
        # Get system admin credentials from environment variables
        system_admin_username = os.environ.get("SYSTEM_ADMIN_USERNAME")
        system_admin_password = os.environ.get("SYSTEM_ADMIN_PASSWORD")
        
        if (system_admin_username and system_admin_password and 
            system_admin_username == user_credentials.username and
            system_admin_password == user_credentials.password):
            
            logger.info("System admin login successful")
            # Create access token for system admin
            access_token = create_access_token(data={"sub": user_credentials.username})
            return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"System admin login check failed: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Check regular users in database
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

# System admin authentication now uses environment variables for better production deployment compatibility

# Certificate Verification Endpoints
@api_router.post("/certificates/upload")
async def upload_certificate(
    file: UploadFile = File(...),
    requester_organization: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Upload and process certificate for verification"""
    try:
        # Validate file type
        allowed_types = ['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'bmp']
        file_type = file.filename.split('.')[-1].lower()
        
        if file_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file_type}' not supported. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Create uploads directory if it doesn't exist
        uploads_dir = Path("/app/uploads")
        uploads_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_path = uploads_dir / f"{file_id}.{file_type}"
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = file_path.stat().st_size
        
        # Create verification request
        verification_request = VerificationRequest(
            requester_id=current_user.id,
            requester_name=current_user.full_name,
            requester_organization=requester_organization,
            file_path=str(file_path),
            file_type=file_type,
            file_size=file_size,
            verification_status="processing"
        )
        
        # Insert into database
        result = await db.verification_requests.insert_one(verification_request.dict())
        verification_request.id = str(result.inserted_id)
        
        # Process document asynchronously
        try:
            analysis = await process_document(str(file_path), file_type)
            
            # Update verification request with OCR results
            update_data = {
                "ocr_text": analysis.text_extracted,
                "extracted_data": analysis.detected_fields,
                "anomalies_detected": analysis.anomalies,
                "confidence_score": analysis.confidence_score,
                "verification_status": "processed",
                "processed_at": datetime.now(timezone.utc)
            }
            
            await db.verification_requests.update_one(
                {"_id": result.inserted_id},
                {"$set": update_data}
            )
            
        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            await db.verification_requests.update_one(
                {"_id": result.inserted_id},
                {"$set": {
                    "verification_status": "failed",
                    "verification_notes": f"Processing error: {str(e)}",
                    "processed_at": datetime.now(timezone.utc)
                }}
            )
        
        return {
            "message": "File uploaded and processing initiated",
            "verification_id": verification_request.id,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@api_router.get("/certificates/verify/{verification_id}")
async def get_verification_status(
    verification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get verification status and results"""
    try:
        # Find verification request
        verification = await db.verification_requests.find_one({"id": verification_id})
        
        if not verification:
            raise HTTPException(status_code=404, detail="Verification request not found")
        
        # Check if user has access (requester or admin roles)
        if (verification["requester_id"] != current_user.id and 
            current_user.role not in ["system_admin", "verifier"]):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Attempt certificate matching if processed
        if verification["verification_status"] == "processed":
            try:
                match_result = await match_certificate(verification["extracted_data"])
                
                # Update verification with match results
                update_data = {
                    "verification_status": "verified" if match_result["is_authentic"] else "rejected",
                    "matched_certificate_id": match_result.get("certificate_id"),
                    "verification_notes": match_result.get("notes", "")
                }
                
                await db.verification_requests.update_one(
                    {"id": verification_id},
                    {"$set": update_data}
                )
                
                verification.update(update_data)
                
            except Exception as e:
                logger.error(f"Certificate matching failed: {str(e)}")
        
        return {
            "verification_id": verification_id,
            "status": verification["verification_status"],
            "confidence_score": verification.get("confidence_score"),
            "extracted_data": verification.get("extracted_data", {}),
            "anomalies": verification.get("anomalies_detected", []),
            "matched_certificate": verification.get("matched_certificate_id"),
            "notes": verification.get("verification_notes", ""),
            "created_at": verification["created_at"],
            "processed_at": verification.get("processed_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Verification lookup failed: {str(e)}")

@api_router.post("/institutions")
async def create_institution(
    institution: InstitutionCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new institution (system_admin only)"""
    if current_user.role != "system_admin":
        raise HTTPException(status_code=403, detail="Only system administrators can create institutions")
    
    try:
        # Check if institution code already exists
        existing = await db.institutions.find_one({"code": institution.code})
        if existing:
            raise HTTPException(status_code=400, detail="Institution code already exists")
        
        # Generate verification hash
        institution_data = institution.dict()
        verification_hash = generate_certificate_hash(institution_data)
        
        new_institution = Institution(
            **institution_data,
            verification_hash=verification_hash
        )
        
        result = await db.institutions.insert_one(new_institution.dict())
        new_institution.id = str(result.inserted_id)
        
        return {
            "message": "Institution created successfully",
            "institution_id": new_institution.id,
            "verification_hash": verification_hash
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Institution creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Institution creation failed: {str(e)}")

@api_router.get("/institutions")
async def list_institutions(
    current_user: User = Depends(get_current_user)
):
    """List all institutions"""
    try:
        institutions = []
        async for institution in db.institutions.find({}):
            institutions.append({
                "id": institution["id"],
                "name": institution["name"],
                "code": institution["code"],
                "type": institution["type"],
                "state": institution["state"],
                "city": institution["city"],
                "is_verified": institution["is_verified"]
            })
        
        return {"institutions": institutions}
        
    except Exception as e:
        logger.error(f"Institution listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Institution listing failed: {str(e)}")

@api_router.post("/institutions/{institution_id}/certificates/upload")
async def upload_certificates_csv(
    institution_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload certificates in CSV format (institution_admin or system_admin only)"""
    if current_user.role not in ["institution_admin", "system_admin"]:
        raise HTTPException(status_code=403, detail="Only institution admins can upload certificates")
    
    # For institution_admin, check if they belong to this institution
    if current_user.role == "institution_admin" and current_user.institution_id != institution_id:
        raise HTTPException(status_code=403, detail="Access denied to this institution")
    
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        # Read CSV file
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        certificates_added = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Validate required fields
                required_fields = ['certificate_id', 'student_name', 'roll_number', 'course_name', 'passing_year']
                missing_fields = [field for field in required_fields if not row.get(field)]
                
                if missing_fields:
                    errors.append(f"Row {row_num}: Missing fields: {', '.join(missing_fields)}")
                    continue
                
                # Get institution info
                institution = await db.institutions.find_one({"id": institution_id})
                if not institution:
                    raise HTTPException(status_code=404, detail="Institution not found")
                
                # Create certificate
                certificate_data = {
                    "certificate_id": row["certificate_id"],
                    "student_name": row["student_name"],
                    "father_name": row.get("father_name", ""),
                    "roll_number": row["roll_number"],
                    "registration_number": row.get("registration_number", ""),
                    "course_name": row["course_name"],
                    "course_type": row.get("course_type", "degree"),
                    "course_duration": row.get("course_duration", ""),
                    "passing_year": int(row["passing_year"]),
                    "grade": row.get("grade", ""),
                    "percentage": float(row["percentage"]) if row.get("percentage") else None,
                    "cgpa": float(row["cgpa"]) if row.get("cgpa") else None,
                    "institution_id": institution_id,
                    "institution_name": institution["name"],
                    "issued_date": datetime.strptime(row.get("issued_date", f"{row['passing_year']}-06-01"), "%Y-%m-%d") if row.get("issued_date") else datetime(int(row["passing_year"]), 6, 1),
                    "metadata": {key: value for key, value in row.items() if key not in required_fields}
                }
                
                # Generate certificate hash
                certificate_data["certificate_hash"] = generate_certificate_hash(certificate_data)
                
                certificate = Certificate(**certificate_data)
                
                # Check for duplicates
                existing = await db.certificates.find_one({
                    "certificate_id": certificate.certificate_id,
                    "institution_id": institution_id
                })
                
                if existing:
                    errors.append(f"Row {row_num}: Certificate ID {certificate.certificate_id} already exists")
                    continue
                
                # Insert certificate
                await db.certificates.insert_one(certificate.dict())
                certificates_added += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        return {
            "message": "CSV processing completed",
            "certificates_added": certificates_added,
            "errors": errors[:50]  # Limit errors to first 50
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CSV upload failed: {str(e)}")

async def match_certificate(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Match extracted certificate data against database"""
    try:
        # Build query based on available fields
        query_conditions = []
        
        if "name" in extracted_data:
            query_conditions.append({"student_name": {"$regex": extracted_data["name"], "$options": "i"}})
        
        if "roll_number" in extracted_data:
            query_conditions.append({"roll_number": extracted_data["roll_number"]})
        
        if "course" in extracted_data:
            query_conditions.append({"course_name": {"$regex": extracted_data["course"], "$options": "i"}})
        
        if "year" in extracted_data:
            try:
                year = int(extracted_data["year"])
                query_conditions.append({"passing_year": year})
            except ValueError:
                pass
        
        if not query_conditions:
            return {
                "is_authentic": False,
                "certificate_id": None,
                "notes": "Insufficient data for matching"
            }
        
        # Search for matching certificates
        query = {"$and": query_conditions} if len(query_conditions) > 1 else query_conditions[0]
        
        certificates = []
        async for cert in db.certificates.find(query).limit(10):
            certificates.append(cert)
        
        if not certificates:
            return {
                "is_authentic": False,
                "certificate_id": None,
                "notes": "No matching certificate found in database"
            }
        
        # Calculate similarity scores for each certificate
        best_match = None
        best_score = 0
        
        for cert in certificates:
            score = calculate_similarity_score(extracted_data, cert)
            if score > best_score:
                best_score = score
                best_match = cert
        
        # Threshold for considering a match authentic
        threshold = 0.7
        
        if best_score >= threshold:
            return {
                "is_authentic": True,
                "certificate_id": best_match["id"],
                "similarity_score": best_score,
                "notes": f"Match found with {best_score:.2f} similarity"
            }
        else:
            return {
                "is_authentic": False,
                "certificate_id": None,
                "similarity_score": best_score,
                "notes": f"Low similarity score: {best_score:.2f} (threshold: {threshold})"
            }
        
    except Exception as e:
        logger.error(f"Certificate matching failed: {str(e)}")
        return {
            "is_authentic": False,
            "certificate_id": None,
            "notes": f"Matching error: {str(e)}"
        }

def calculate_similarity_score(extracted_data: Dict[str, Any], certificate: Dict[str, Any]) -> float:
    """Calculate similarity score between extracted data and certificate"""
    scores = []
    
    # Name similarity
    if "name" in extracted_data and certificate.get("student_name"):
        name_similarity = textdistance.jaro_winkler(
            extracted_data["name"].lower(),
            certificate["student_name"].lower()
        )
        scores.append(name_similarity * 0.3)  # 30% weight
    
    # Roll number exact match
    if "roll_number" in extracted_data and certificate.get("roll_number"):
        if extracted_data["roll_number"].lower() == certificate["roll_number"].lower():
            scores.append(0.25)  # 25% weight
    
    # Course similarity
    if "course" in extracted_data and certificate.get("course_name"):
        course_similarity = textdistance.jaro_winkler(
            extracted_data["course"].lower(),
            certificate["course_name"].lower()
        )
        scores.append(course_similarity * 0.2)  # 20% weight
    
    # Year exact match
    if "year" in extracted_data and certificate.get("passing_year"):
        try:
            if int(extracted_data["year"]) == certificate["passing_year"]:
                scores.append(0.15)  # 15% weight
        except ValueError:
            pass
    
    # Grade similarity
    if "grade" in extracted_data and certificate.get("grade"):
        if extracted_data["grade"].lower() == certificate["grade"].lower():
            scores.append(0.1)  # 10% weight
    
    return sum(scores) if scores else 0

# Add CORS middleware BEFORE including router
cors_origins_str = os.environ.get('CORS_ORIGINS', '*')
raw_origins = [origin.strip() for origin in cors_origins_str.split(',')]

allowed_origins = []
allowed_origins_regex = []

for origin in raw_origins:
    if "*" in origin:
        # Convert wildcard to a valid regex pattern
        regex = origin.replace(".", r"\.").replace("*", ".*")
        allowed_origins_regex.append(regex)
    else:
        allowed_origins.append(origin)

# Combine all regex patterns into a single regex string
final_regex = "|".join(allowed_origins_regex) if allowed_origins_regex else None

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=final_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router in the main app
app.include_router(api_router)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
