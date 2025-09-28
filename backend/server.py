from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from pymongo import ASCENDING

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create the main app
app = FastAPI(title="Work Hours Tracker")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    phone: str
    password_hash: str
    role: str = "employee"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str

class UserLogin(BaseModel):
    email_or_phone: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class WorkSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    is_half_day: bool = False
    total_break_seconds: int = 0
    effective_seconds: int = 0
    notes: Optional[str] = None

class Break(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None

class Timesheet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    task_id: str
    work_description: str
    status: str  # Completed/Ongoing/Blocked
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TimesheetCreate(BaseModel):
    task_id: str
    work_description: str
    status: str

class SessionResponse(BaseModel):
    session: WorkSession
    active_break: Optional[Break] = None
    effective_seconds: int
    eta_logout_utc: Optional[datetime] = None
    can_logout: bool = False

# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user)

def calculate_effective_seconds(session_start: datetime, breaks: List[dict]) -> int:
    """Calculate effective work seconds excluding breaks"""
    now = datetime.now(timezone.utc)
    total_time = (now - session_start).total_seconds()
    
    break_seconds = 0
    for break_item in breaks:
        if break_item.get('end_time'):
            # Closed break
            break_duration = (break_item['end_time'] - break_item['start_time']).total_seconds()
            break_seconds += break_duration
        else:
            # Active break
            break_duration = (now - break_item['start_time']).total_seconds()
            break_seconds += break_duration
    
    return max(0, int(total_time - break_seconds))

# Authentication routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({
        "$or": [{"email": user_data.email}, {"phone": user_data.phone}]
    })
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user
    user = User(
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=hash_password(user_data.password)
    )
    
    await db.users.insert_one(user.dict())
    
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.post("/auth/login", response_model=Token)
async def login(login_data: UserLogin):
    # Find user by email or phone
    user_doc = await db.users.find_one({
        "$or": [
            {"email": login_data.email_or_phone},
            {"phone": login_data.email_or_phone}
        ]
    })
    
    if not user_doc or not verify_password(login_data.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user_doc["id"]})
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Session routes
@api_router.post("/sessions/start", response_model=WorkSession)
async def start_session(current_user: User = Depends(get_current_user)):
    # Check if user already has an active session
    active_session = await db.sessions.find_one({
        "user_id": current_user.id,
        "end_time": None
    })
    
    if active_session:
        raise HTTPException(status_code=409, detail="Active session already exists")
    
    session = WorkSession(
        user_id=current_user.id,
        start_time=datetime.now(timezone.utc)
    )
    
    await db.sessions.insert_one(session.dict())
    return session

@api_router.post("/sessions/end")
async def end_session(
    timesheet_data: TimesheetCreate,
    current_user: User = Depends(get_current_user)
):
    # Find active session
    session_doc = await db.sessions.find_one({
        "user_id": current_user.id,
        "end_time": None
    })
    
    if not session_doc:
        raise HTTPException(status_code=404, detail="No active session found")
    
    session = WorkSession(**session_doc)
    
    # Get all breaks for this session
    breaks = await db.breaks.find({"session_id": session.id}).to_list(length=None)
    
    # Calculate effective seconds
    effective_seconds = calculate_effective_seconds(session.start_time, breaks)
    
    # Check if user has worked enough (9 hours = 32400 seconds)
    required_seconds = 9 * 60 * 60  # 9 hours
    if effective_seconds < required_seconds and not session.is_half_day:
        raise HTTPException(
            status_code=422, 
            detail=f"Need to work {required_seconds - effective_seconds} more seconds or apply half day"
        )
    
    # End session
    now = datetime.now(timezone.utc)
    total_break_seconds = sum([
        (b.get('end_time', now) - b['start_time']).total_seconds() 
        for b in breaks
    ])
    
    await db.sessions.update_one(
        {"id": session.id},
        {
            "$set": {
                "end_time": now,
                "effective_seconds": effective_seconds,
                "total_break_seconds": int(total_break_seconds)
            }
        }
    )
    
    # Create timesheet
    timesheet = Timesheet(
        session_id=session.id,
        task_id=timesheet_data.task_id,
        work_description=timesheet_data.work_description,
        status=timesheet_data.status
    )
    
    await db.timesheets.insert_one(timesheet.dict())
    
    return {"message": "Session ended successfully"}

@api_router.get("/sessions/active", response_model=Optional[SessionResponse])
async def get_active_session(current_user: User = Depends(get_current_user)):
    # Find active session
    session_doc = await db.sessions.find_one({
        "user_id": current_user.id,
        "end_time": None
    })
    
    if not session_doc:
        return None
    
    session = WorkSession(**session_doc)
    
    # Get breaks for this session
    breaks = await db.breaks.find({"session_id": session.id}).to_list(length=None)
    
    # Find active break
    active_break = None
    for break_doc in breaks:
        if break_doc.get('end_time') is None:
            active_break = Break(**break_doc)
            break
    
    # Calculate effective seconds
    effective_seconds = calculate_effective_seconds(session.start_time, breaks)
    
    # Calculate ETA logout
    required_seconds = 9 * 60 * 60  # 9 hours
    remaining_seconds = max(0, required_seconds - effective_seconds)
    
    eta_logout_utc = None
    can_logout = effective_seconds >= required_seconds
    
    if remaining_seconds > 0:
        eta_logout_utc = datetime.now(timezone.utc) + timedelta(seconds=remaining_seconds)
    
    return SessionResponse(
        session=session,
        active_break=active_break,
        effective_seconds=effective_seconds,
        eta_logout_utc=eta_logout_utc,
        can_logout=can_logout
    )

# Break routes
@api_router.post("/breaks/start", response_model=Break)
async def start_break(current_user: User = Depends(get_current_user)):
    # Find active session
    session_doc = await db.sessions.find_one({
        "user_id": current_user.id,
        "end_time": None
    })
    
    if not session_doc:
        raise HTTPException(status_code=404, detail="No active session found")
    
    # Check if there's already an active break
    active_break = await db.breaks.find_one({
        "session_id": session_doc["id"],
        "end_time": None
    })
    
    if active_break:
        raise HTTPException(status_code=409, detail="Break already active")
    
    break_obj = Break(
        session_id=session_doc["id"],
        start_time=datetime.now(timezone.utc)
    )
    
    await db.breaks.insert_one(break_obj.dict())
    return break_obj

@api_router.post("/breaks/end")
async def end_break(current_user: User = Depends(get_current_user)):
    # Find active session
    session_doc = await db.sessions.find_one({
        "user_id": current_user.id,
        "end_time": None
    })
    
    if not session_doc:
        raise HTTPException(status_code=404, detail="No active session found")
    
    # Find active break
    break_doc = await db.breaks.find_one({
        "session_id": session_doc["id"],
        "end_time": None
    })
    
    if not break_doc:
        raise HTTPException(status_code=404, detail="No active break found")
    
    await db.breaks.update_one(
        {"id": break_doc["id"]},
        {"$set": {"end_time": datetime.now(timezone.utc)}}
    )
    
    return {"message": "Break ended successfully"}

# Half day route
@api_router.post("/leaves/half-day")
async def apply_half_day(
    timesheet_data: TimesheetCreate,
    current_user: User = Depends(get_current_user)
):
    # Find active session
    session_doc = await db.sessions.find_one({
        "user_id": current_user.id,
        "end_time": None
    })
    
    if not session_doc:
        raise HTTPException(status_code=404, detail="No active session found")
    
    session = WorkSession(**session_doc)
    
    # Mark session as half day and end it
    now = datetime.now(timezone.utc)
    breaks = await db.breaks.find({"session_id": session.id}).to_list(length=None)
    effective_seconds = calculate_effective_seconds(session.start_time, breaks)
    total_break_seconds = sum([
        (b.get('end_time', now) - b['start_time']).total_seconds() 
        for b in breaks
    ])
    
    await db.sessions.update_one(
        {"id": session.id},
        {
            "$set": {
                "end_time": now,
                "is_half_day": True,
                "effective_seconds": effective_seconds,
                "total_break_seconds": int(total_break_seconds)
            }
        }
    )
    
    # Create timesheet
    timesheet = Timesheet(
        session_id=session.id,
        task_id=timesheet_data.task_id,
        work_description=timesheet_data.work_description,
        status=timesheet_data.status
    )
    
    await db.timesheets.insert_one(timesheet.dict())
    
    # Create half-day leave record
    leave_record = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "date": session.start_time.date().isoformat(),
        "type": "half",
        "reason": "Half day application",
        "status": "approved"
    }
    
    await db.leaves.insert_one(leave_record)
    
    return {"message": "Half day applied and session ended successfully"}

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

@app.on_event("startup")
async def startup_db():
    # Create indexes
    await db.users.create_index([("email", ASCENDING)], unique=True)
    await db.users.create_index([("phone", ASCENDING)], unique=True)
    await db.sessions.create_index([("user_id", ASCENDING)])
    await db.breaks.create_index([("session_id", ASCENDING)])

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()