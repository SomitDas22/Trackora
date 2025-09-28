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
import calendar as cal

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

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

class EmployeeCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str
    dob: str = ""
    blood_group: str = ""
    emergency_contact: str = ""
    address: str = ""
    aadhar_card: str = ""
    designation: str = ""
    department: str = ""
    joining_date: str = ""
    release_date: str = ""

class EmployeeUpdate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    dob: str = ""
    blood_group: str = ""
    emergency_contact: str = ""
    address: str = ""
    aadhar_card: str = ""
    designation: str = ""
    department: str = ""
    joining_date: str = ""
    release_date: str = ""

class UserLogin(BaseModel):
    email_or_phone: str
    password: str

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class AdminCreate(BaseModel):
    name: str
    email: EmailStr
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

class DepartmentCreate(BaseModel):
    name: str
    description: str = ""

class ManagerCreate(BaseModel):
    employee_id: str  # Employee who becomes manager
    department_id: str

class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    department_id: str
    manager_id: str
    employee_ids: List[str] = []
    start_date: str = ""
    end_date: str = ""
    status: str = "Active"  # Active, Completed, On Hold

class OrganizationSettings(BaseModel):
    company_name: str
    company_logo: str = ""  # Base64 encoded or file path
    establishment_date: str = ""
    company_email: str = ""
    founder_name: str = ""
    founder_email: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""

class OrganizationUpdate(BaseModel):
    company_name: str
    establishment_date: str = ""
    company_email: str = ""
    founder_name: str = ""
    founder_email: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""

class LeaveApplication(BaseModel):
    leave_type: str  # Casual, Sick, LWP
    start_date: str
    end_date: str
    reason: str
    days_count: float

class ITTicket(BaseModel):
    title: str
    description: str
    category: str  # Hardware, Software, Network, Account, Other
    priority: str = "Medium"  # Low, Medium, High, Critical

class ITTicketCreate(BaseModel):
    title: str
    description: str
    category: str
    priority: str = "Medium"

class LeaveApplicationCreate(BaseModel):
    leave_type: str  # Casual Leave, Sick Leave, Leave without Pay
    start_date: str
    end_date: str
    reason: str
    days_count: float

class LeaveApprovalRequest(BaseModel):
    status: str  # approved, rejected
    manager_reason: str = ""

class LeaveBalance(BaseModel):
    user_id: str
    casual_leave: int = 0
    sick_leave: int = 0
    leave_without_pay: int = 0
    used_casual_leave: int = 0
    used_sick_leave: int = 0
    used_leave_without_pay: int = 0

class LeaveSettings(BaseModel):
    casual_leave_quarterly: int = 2
    sick_leave_quarterly: int = 2
    leave_without_pay_quarterly: int = 5

class ProjectAssignment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    employee_id: str
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
    
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
        
    return User(**user)

def calculate_effective_seconds(session_start: datetime, breaks: List[dict]) -> int:
    """Calculate effective work seconds excluding breaks"""
    now = datetime.now(timezone.utc)
    
    # Ensure session_start is timezone-aware
    if session_start.tzinfo is None:
        session_start = session_start.replace(tzinfo=timezone.utc)
    
    total_time = (now - session_start).total_seconds()
    
    break_seconds = 0
    for break_item in breaks:
        break_start = break_item['start_time']
        if break_start.tzinfo is None:
            break_start = break_start.replace(tzinfo=timezone.utc)
            
        if break_item.get('end_time'):
            # Closed break
            break_end = break_item['end_time']
            if break_end.tzinfo is None:
                break_end = break_end.replace(tzinfo=timezone.utc)
            break_duration = (break_end - break_start).total_seconds()
            break_seconds += break_duration
        else:
            # Active break
            break_duration = (now - break_start).total_seconds()
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

# Admin Authentication routes
@api_router.post("/admin/auth/login", response_model=Token)
async def admin_login(login_data: AdminLogin):
    # Find admin by email
    user_doc = await db.users.find_one({
        "email": login_data.email,
        "role": "admin"
    })
    
    if not user_doc or not verify_password(login_data.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    access_token = create_access_token(data={"sub": user_doc["id"]})
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.post("/admin/auth/create", response_model=Token)
async def create_admin(admin_data: AdminCreate):
    # Check if admin exists
    existing_admin = await db.users.find_one({"email": admin_data.email})
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin already exists")
    
    # Create admin user
    admin = User(
        name=admin_data.name,
        email=admin_data.email,
        phone="",  # Admins don't need phone
        password_hash=hash_password(admin_data.password),
        role="admin"
    )
    
    await db.users.insert_one(admin.dict())
    
    access_token = create_access_token(data={"sub": admin.id})
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/admin/auth/me", response_model=User)
async def get_admin_me(current_admin: User = Depends(get_current_admin)):
    return current_admin

# Session routes
@api_router.get("/sessions/can-start-today")
async def can_start_session_today(current_user: User = Depends(get_current_user)):
    """Check if user can start a new session today"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Check if user has any session for today
    existing_session = await db.sessions.find_one({
        "user_id": current_user.id,
        "start_time": {"$gte": today_start, "$lte": today_end}
    })
    
    if existing_session:
        return {
            "can_start": False,
            "reason": "Already logged in today" if existing_session.get("end_time") else "Active session exists",
            "session_date": existing_session["start_time"].date().isoformat(),
            "session_time": existing_session["start_time"].strftime("%H:%M:%S"),
            "is_completed": existing_session.get("end_time") is not None
        }
    
    return {
        "can_start": True,
        "reason": "No session found for today"
    }

@api_router.post("/sessions/start", response_model=WorkSession)
async def start_session(current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Check if user already has ANY session for today (active or completed)
    existing_session = await db.sessions.find_one({
        "user_id": current_user.id,
        "start_time": {"$gte": today_start, "$lte": today_end}
    })
    
    if existing_session:
        if existing_session.get("end_time") is None:
            raise HTTPException(status_code=409, detail="You already have an active session for today")
        else:
            raise HTTPException(status_code=409, detail="You have already logged in today. Only one login per day is allowed.")
    
    session = WorkSession(
        user_id=current_user.id,
        start_time=now
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
    total_break_seconds = 0
    for b in breaks:
        break_start = b['start_time']
        if break_start.tzinfo is None:
            break_start = break_start.replace(tzinfo=timezone.utc)
        
        break_end = b.get('end_time', now)
        if break_end and break_end.tzinfo is None:
            break_end = break_end.replace(tzinfo=timezone.utc)
        elif break_end is None:
            break_end = now
        
        total_break_seconds += (break_end - break_start).total_seconds()
    
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

# History and Calendar routes
@api_router.get("/sessions/history")
async def get_session_history(
    from_date: str = None,
    to_date: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get session history for the user"""
    query = {"user_id": current_user.id, "end_time": {"$ne": None}}
    
    # Add date filters if provided
    if from_date:
        start_date = datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc)
        query["start_time"] = {"$gte": start_date}
    
    if to_date:
        end_date = datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc)
        if "start_time" in query:
            query["start_time"]["$lte"] = end_date
        else:
            query["start_time"] = {"$lte": end_date}
    
    sessions = await db.sessions.find(query).sort("start_time", -1).to_list(length=100)
    
    history = []
    for session_doc in sessions:
        session = WorkSession(**session_doc)
        
        # Get breaks for this session
        breaks = await db.breaks.find({"session_id": session.id}).to_list(length=None)
        break_count = len(breaks)
        total_break_seconds = session.total_break_seconds
        
        # Get timesheet
        timesheet = await db.timesheets.find_one({"session_id": session.id})
        
        # Determine day type
        day_type = "Half Day" if session.is_half_day else "Full Work Day"
        
        history_item = {
            "id": session.id,
            "date": session.start_time.date().isoformat(),
            "login_time": session.start_time.strftime("%H:%M:%S"),
            "logout_time": session.end_time.strftime("%H:%M:%S") if session.end_time else None,
            "total_duration": str(timedelta(seconds=int((session.end_time - session.start_time).total_seconds()))) if session.end_time else None,
            "effective_duration": str(timedelta(seconds=session.effective_seconds)),
            "break_count": break_count,
            "break_duration": str(timedelta(seconds=int(total_break_seconds))),
            "day_type": day_type,
            "timesheet_status": "Submitted" if timesheet else "Missing"
        }
        history.append(history_item)
    
    return history

@api_router.get("/calendar/month")
async def get_calendar_month(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user)
):
    """Get calendar data for a specific month with correct status colors"""
    from calendar import monthrange
    import calendar as cal
    
    # Get first and last day of the month
    first_day = datetime(year, month, 1, tzinfo=timezone.utc)
    last_day_num = monthrange(year, month)[1]
    last_day = datetime(year, month, last_day_num, 23, 59, 59, tzinfo=timezone.utc)
    
    # Get all sessions for the month for this user
    sessions = await db.sessions.find({
        "user_id": current_user.id,
        "start_time": {"$gte": first_day, "$lte": last_day},
        "end_time": {"$ne": None}
    }).to_list(length=None)
    
    # Get all leaves for the month for this user
    leaves = await db.leaves.find({
        "user_id": current_user.id,
        "date": {
            "$gte": first_day.date().isoformat(),
            "$lte": last_day.date().isoformat()
        }
    }).to_list(length=None)
    
    # Get holidays for the month (prioritize mandatory holidays)
    holidays = await db.holidays.find({
        "date": {
            "$gte": first_day.date().isoformat(),
            "$lte": last_day.date().isoformat()
        }
    }).to_list(length=None)
    
    # Build calendar data with priority logic
    calendar_days = []
    for day in range(1, last_day_num + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        day_type = None
        detail_info = {}
        
        # Priority 1: Check if user worked (Green) or had half-day (Orange)
        user_session = None
        for session in sessions:
            if session["start_time"].date().isoformat() == date_str:
                user_session = session
                break
        
        if user_session:
            if user_session.get("is_half_day"):
                day_type = "half-day"  # Orange
                detail_info = {
                    "login_time": user_session["start_time"].strftime("%H:%M"),
                    "logout_time": user_session.get("end_time", "").strftime("%H:%M") if user_session.get("end_time") else "",
                    "effective_hours": round(user_session.get("effective_seconds", 0) / 3600, 2),
                    "status": "Half Day Worked"
                }
            else:
                day_type = "worked"  # Green
                detail_info = {
                    "login_time": user_session["start_time"].strftime("%H:%M"),
                    "logout_time": user_session.get("end_time", "").strftime("%H:%M") if user_session.get("end_time") else "",
                    "effective_hours": round(user_session.get("effective_seconds", 0) / 3600, 2),
                    "status": "Full Day Worked"
                }
        
        # Priority 2: Check if user was on leave (Red)
        elif any(l["date"] == date_str for l in leaves):
            leave = next(l for l in leaves if l["date"] == date_str)
            if leave["type"] == "half":
                day_type = "half-day"  # Orange (but this case should be covered above if there's a session)
                detail_info = {
                    "status": "Half Day Leave",
                    "reason": leave.get("reason", "Half day application")
                }
            else:
                day_type = "leave"  # Red
                detail_info = {
                    "status": "Full Day Leave",
                    "reason": leave.get("reason", "Leave application")
                }
        
        # Priority 3: Check if it's a holiday (Yellow) - prioritize mandatory holidays
        elif any(h["date"] == date_str for h in holidays):
            holiday = next(h for h in holidays if h["date"] == date_str)
            holiday_type = holiday.get("type", "Mandatory")  # Default to Mandatory for backward compatibility
            day_type = "holiday"  # Yellow
            detail_info = {
                "status": f"{holiday_type} Holiday",
                "holiday_name": holiday["name"]
            }
        
        # Priority 4: Regular working day (no special status)
        else:
            day_type = None
            detail_info = {
                "status": "Available"
            }
        
        calendar_days.append({
            "date": date_str,
            "day": day,
            "type": day_type,
            "weekday": cal.weekday(year, month, day),
            "details": detail_info
        })
    
    return {
        "year": year,
        "month": month,
        "days": calendar_days,
        "legend": {
            "worked": "Green - Full Day Worked",
            "half-day": "Orange - Half Day Worked/Leave",
            "leave": "Red - Full Day Leave",
            "holiday": "Yellow - Mandatory Holiday",
            "available": "No Color - Available Day"
        }
    }

@api_router.get("/holidays")
async def get_holidays(year: int):
    """Get holidays for a specific year"""
    holidays = await db.holidays.find({
        "date": {"$regex": f"^{year}"}
    }).to_list(length=None)
    return holidays

# Dashboard stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(
    year: int = None,
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics"""
    if not year:
        year = datetime.now().year
    
    # Get leave counts by month
    leaves_by_month = []
    for month in range(1, 13):
        month_start = f"{year}-{month:02d}-01"
        if month == 12:
            month_end = f"{year + 1}-01-01"
        else:
            month_end = f"{year}-{month + 1:02d}-01"
        
        leave_count = await db.leaves.count_documents({
            "user_id": current_user.id,
            "date": {"$gte": month_start, "$lt": month_end}
        })
        
        leaves_by_month.append({
            "month": month,
            "month_name": cal.month_name[month],
            "leaves_count": leave_count
        })
    
    return {"leaves_by_month": leaves_by_month}

# Admin Panel routes
@api_router.get("/admin/admin-users")
async def get_all_admin_users(current_admin: User = Depends(get_current_admin)):
    """Get all admin users"""
    admins = await db.users.find({"role": "admin"}).to_list(length=None)
    
    admin_list = []
    for admin_doc in admins:
        admin_user = User(**admin_doc)
        admin_stats = {
            "id": admin_user.id,
            "name": admin_user.name,
            "email": admin_user.email,
            "created_at": admin_user.created_at.isoformat(),
            "status": "Active"
        }
        admin_list.append(admin_stats)
    
    return admin_list

@api_router.post("/admin/create-admin")
async def create_new_admin(admin_data: AdminCreate, current_admin: User = Depends(get_current_admin)):
    """Create a new admin user"""
    # Check if admin exists
    existing_admin = await db.users.find_one({"email": admin_data.email})
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin with this email already exists")
    
    # Create admin user
    new_admin = User(
        name=admin_data.name,
        email=admin_data.email,
        phone="",
        password_hash=hash_password(admin_data.password),
        role="admin"
    )
    
    await db.users.insert_one(new_admin.dict())
    return {"message": "Admin created successfully", "admin_id": new_admin.id}

@api_router.get("/admin/holidays-management")
async def get_holidays_management(current_admin: User = Depends(get_current_admin)):
    """Get all holidays for management"""
    current_year = datetime.now().year
    holidays_docs = await db.holidays.find({}, {"_id": 0}).sort("date", 1).to_list(length=None)
    
    # Clean holidays data
    holidays = []
    for h in holidays_docs:
        holidays.append({
            "id": h.get("id", ""),
            "name": h.get("name", ""),
            "date": h.get("date", ""),
            "type": h.get("type", "Mandatory")
        })
    
    return {
        "total_holidays": len(holidays),
        "holidays_this_year": len([h for h in holidays if h["date"].startswith(str(current_year))]),
        "holidays": holidays
    }

class HolidayCreate(BaseModel):
    name: str
    date: str
    type: str = "Mandatory"  # Mandatory or Optional

class HolidayUpdate(BaseModel):
    name: str
    date: str
    type: str

@api_router.post("/admin/add-holiday")
async def add_holiday(holiday_data: HolidayCreate, current_admin: User = Depends(get_current_admin)):
    """Add a new holiday"""
    new_holiday = {
        "id": str(uuid.uuid4()),
        "date": holiday_data.date,
        "name": holiday_data.name,
        "type": holiday_data.type
    }
    
    # Check if holiday already exists for this date
    existing = await db.holidays.find_one({"date": holiday_data.date})
    if existing:
        raise HTTPException(status_code=400, detail="Holiday already exists for this date")
    
    await db.holidays.insert_one(new_holiday)
    return {"message": "Holiday added successfully", "holiday_id": new_holiday["id"]}

@api_router.put("/admin/update-holiday/{holiday_id}")
async def update_holiday(holiday_id: str, holiday_data: HolidayUpdate, current_admin: User = Depends(get_current_admin)):
    """Update a holiday"""
    # Check if holiday exists
    existing_holiday = await db.holidays.find_one({"id": holiday_id})
    if not existing_holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    
    # Check if date is already taken by another holiday
    date_check = await db.holidays.find_one({"date": holiday_data.date, "id": {"$ne": holiday_id}})
    if date_check:
        raise HTTPException(status_code=400, detail="Another holiday already exists for this date")
    
    # Update holiday
    await db.holidays.update_one(
        {"id": holiday_id},
        {"$set": {"name": holiday_data.name, "date": holiday_data.date, "type": holiday_data.type}}
    )
    
    return {"message": "Holiday updated successfully"}

@api_router.delete("/admin/holiday/{holiday_id}")
async def delete_holiday(holiday_id: str, current_admin: User = Depends(get_current_admin)):
    """Delete a holiday"""
    result = await db.holidays.delete_one({"id": holiday_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Holiday not found")
    
    return {"message": "Holiday deleted successfully"}

@api_router.get("/admin/users-on-leave")
async def get_users_on_leave(current_admin: User = Depends(get_current_admin)):
    """Get users currently on leave or recent leave data"""
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    
    # Get users with half-day leaves today
    today_leaves = await db.leaves.find({"date": today}).to_list(length=None)
    
    # Get users with recent half-day applications (last 7 days)
    week_ago = (now - timedelta(days=7)).date().isoformat()
    recent_leaves = await db.leaves.find({
        "date": {"$gte": week_ago, "$lte": today}
    }).to_list(length=None)
    
    # Get detailed user info for leaves
    leave_users = []
    for leave in recent_leaves:
        user = await db.users.find_one({"id": leave["user_id"]})
        if user:
            leave_users.append({
                "user_id": leave["user_id"],
                "user_name": user["name"],
                "user_email": user["email"],
                "leave_date": leave["date"],
                "leave_type": leave["type"],
                "reason": leave.get("reason", "Half day application"),
                "status": leave.get("status", "approved")
            })
    
    return {
        "users_on_leave_today": len(today_leaves),
        "total_leaves_this_week": len(recent_leaves),
        "leave_details": leave_users
    }

class AdminUpdate(BaseModel):
    name: str
    email: EmailStr

@api_router.put("/admin/update-admin/{admin_id}")
async def update_admin(admin_id: str, admin_data: AdminUpdate, current_admin: User = Depends(get_current_admin)):
    """Update admin user details"""
    # Check if admin exists
    existing_admin = await db.users.find_one({"id": admin_id, "role": "admin"})
    if not existing_admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    # Check if email is already taken by another user
    email_check = await db.users.find_one({"email": admin_data.email, "id": {"$ne": admin_id}})
    if email_check:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Update admin
    await db.users.update_one(
        {"id": admin_id},
        {"$set": {"name": admin_data.name, "email": admin_data.email}}
    )
    
    return {"message": "Admin updated successfully"}

@api_router.delete("/admin/delete-admin/{admin_id}")
async def delete_admin(admin_id: str, current_admin: User = Depends(get_current_admin)):
    """Delete admin user"""
    # Prevent deleting own account
    if admin_id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
    
    # Check if admin exists
    existing_admin = await db.users.find_one({"id": admin_id, "role": "admin"})
    if not existing_admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    # Check if this is the last admin
    admin_count = await db.users.count_documents({"role": "admin"})
    if admin_count <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the last admin user")
    
    # Delete admin
    result = await db.users.delete_one({"id": admin_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    return {"message": "Admin deleted successfully"}

@api_router.get("/admin/employees")
async def get_all_employees(current_admin: User = Depends(get_current_admin)):
    """Get all employees with detailed information"""
    employees = await db.users.find({"role": "employee"}).to_list(length=None)
    
    employee_list = []
    for emp_doc in employees:
        # Calculate status based on release_date
        status = "Active"
        if emp_doc.get("release_date") and emp_doc["release_date"].strip():
            try:
                release_date = datetime.fromisoformat(emp_doc["release_date"])
                if release_date <= datetime.now():
                    status = "Inactive"
            except:
                pass
        
        # Get session and leave stats
        total_sessions = await db.sessions.count_documents({"user_id": emp_doc["id"], "end_time": {"$ne": None}})
        total_leaves = await db.leaves.count_documents({"user_id": emp_doc["id"]})
        
        employee_data = {
            "id": emp_doc["id"],
            "name": emp_doc["name"],
            "email": emp_doc["email"],
            "phone": emp_doc["phone"],
            "dob": emp_doc.get("dob", ""),
            "blood_group": emp_doc.get("blood_group", ""),
            "emergency_contact": emp_doc.get("emergency_contact", ""),
            "address": emp_doc.get("address", ""),
            "aadhar_card": emp_doc.get("aadhar_card", ""),
            "designation": emp_doc.get("designation", ""),
            "department": emp_doc.get("department", ""),
            "joining_date": emp_doc.get("joining_date", ""),
            "release_date": emp_doc.get("release_date", ""),
            "status": status,
            "created_at": emp_doc["created_at"].isoformat(),
            "total_sessions": total_sessions,
            "total_leaves": total_leaves
        }
        employee_list.append(employee_data)
    
    return employee_list

@api_router.post("/admin/create-employee")
async def create_employee(emp_data: EmployeeCreate, current_admin: User = Depends(get_current_admin)):
    """Create a new employee"""
    # Check if employee exists
    existing_user = await db.users.find_one({
        "$or": [{"email": emp_data.email}, {"phone": emp_data.phone}]
    })
    if existing_user:
        raise HTTPException(status_code=400, detail="Employee with this email or phone already exists")
    
    # Calculate status based on release_date
    status = "Active"
    if emp_data.release_date and emp_data.release_date.strip():
        try:
            release_date = datetime.fromisoformat(emp_data.release_date)
            if release_date <= datetime.now():
                status = "Inactive"
        except:
            pass
    
    # Create employee user
    employee = User(
        name=emp_data.name,
        email=emp_data.email,
        phone=emp_data.phone,
        password_hash=hash_password(emp_data.password),
        role="employee"
    )
    
    # Convert to dict and add additional fields
    emp_dict = employee.dict()
    emp_dict.update({
        "dob": emp_data.dob,
        "blood_group": emp_data.blood_group,
        "emergency_contact": emp_data.emergency_contact,
        "address": emp_data.address,
        "aadhar_card": emp_data.aadhar_card,
        "designation": emp_data.designation,
        "department": emp_data.department,
        "joining_date": emp_data.joining_date,
        "release_date": emp_data.release_date,
        "status": status
    })
    
    await db.users.insert_one(emp_dict)
    return {"message": "Employee created successfully", "employee_id": employee.id}

@api_router.put("/admin/update-employee/{emp_id}")
async def update_employee(emp_id: str, emp_data: EmployeeUpdate, current_admin: User = Depends(get_current_admin)):
    """Update employee details"""
    # Check if employee exists
    existing_emp = await db.users.find_one({"id": emp_id, "role": "employee"})
    if not existing_emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if email/phone is already taken by another user
    email_check = await db.users.find_one({"email": emp_data.email, "id": {"$ne": emp_id}})
    if email_check:
        raise HTTPException(status_code=400, detail="Email already exists")
        
    phone_check = await db.users.find_one({"phone": emp_data.phone, "id": {"$ne": emp_id}})
    if phone_check:
        raise HTTPException(status_code=400, detail="Phone number already exists")
    
    # Calculate status based on release_date
    status = "Active"
    if emp_data.release_date and emp_data.release_date.strip():
        try:
            release_date = datetime.fromisoformat(emp_data.release_date)
            if release_date <= datetime.now():
                status = "Inactive"
        except:
            pass
    
    # Update employee
    update_data = {
        "name": emp_data.name,
        "email": emp_data.email,
        "phone": emp_data.phone,
        "dob": emp_data.dob,
        "blood_group": emp_data.blood_group,
        "emergency_contact": emp_data.emergency_contact,
        "address": emp_data.address,
        "aadhar_card": emp_data.aadhar_card,
        "designation": emp_data.designation,
        "department": emp_data.department,
        "joining_date": emp_data.joining_date,
        "release_date": emp_data.release_date,
        "status": status
    }
    
    await db.users.update_one({"id": emp_id}, {"$set": update_data})
    return {"message": "Employee updated successfully"}

@api_router.delete("/admin/delete-employee/{emp_id}")
async def delete_employee(emp_id: str, current_admin: User = Depends(get_current_admin)):
    """Delete employee"""
    # Check if employee exists
    existing_emp = await db.users.find_one({"id": emp_id, "role": "employee"})
    if not existing_emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Delete employee and related data
    await db.users.delete_one({"id": emp_id})
    await db.sessions.delete_many({"user_id": emp_id})
    await db.leaves.delete_many({"user_id": emp_id})
    
    return {"message": "Employee deleted successfully"}

# Department Management
@api_router.get("/admin/departments")
async def get_all_departments(current_admin: User = Depends(get_current_admin)):
    """Get all departments"""
    departments = await db.departments.find({}, {"_id": 0}).to_list(length=None)
    
    # Add employee and project counts
    for dept in departments:
        managers_count = await db.managers.count_documents({"department_id": dept["id"]})
        projects_count = await db.projects.count_documents({"department_id": dept["id"]})
        dept["managers_count"] = managers_count
        dept["projects_count"] = projects_count
    
    return departments

@api_router.post("/admin/create-department")
async def create_department(dept_data: DepartmentCreate, current_admin: User = Depends(get_current_admin)):
    """Create a new department"""
    new_dept = {
        "id": str(uuid.uuid4()),
        "name": dept_data.name,
        "description": dept_data.description,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Check if department already exists
    existing = await db.departments.find_one({"name": dept_data.name})
    if existing:
        raise HTTPException(status_code=400, detail="Department with this name already exists")
    
    await db.departments.insert_one(new_dept)
    return {"message": "Department created successfully", "department_id": new_dept["id"]}

# Manager Management
@api_router.get("/admin/managers")
async def get_all_managers(current_admin: User = Depends(get_current_admin)):
    """Get all managers with their details"""
    managers = await db.managers.find({}, {"_id": 0}).to_list(length=None)
    
    manager_list = []
    for manager in managers:
        # Get employee details
        employee = await db.users.find_one({"id": manager["employee_id"]})
        department = await db.departments.find_one({"id": manager["department_id"]})
        
        if employee and department:
            manager_info = {
                "id": manager["id"],
                "employee_id": manager["employee_id"],
                "employee_name": employee["name"],
                "employee_email": employee["email"],
                "department_id": manager["department_id"],
                "department_name": department["name"],
                "created_at": manager.get("created_at", "")
            }
            manager_list.append(manager_info)
    
    return manager_list

@api_router.post("/admin/create-manager")
async def create_manager(manager_data: ManagerCreate, current_admin: User = Depends(get_current_admin)):
    """Assign an employee as manager"""
    # Check if employee exists and is not admin
    employee = await db.users.find_one({"id": manager_data.employee_id, "role": "employee"})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if department exists
    department = await db.departments.find_one({"id": manager_data.department_id})
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Check if employee is already a manager
    existing_manager = await db.managers.find_one({"employee_id": manager_data.employee_id})
    if existing_manager:
        raise HTTPException(status_code=400, detail="Employee is already a manager")
    
    new_manager = {
        "id": str(uuid.uuid4()),
        "employee_id": manager_data.employee_id,
        "department_id": manager_data.department_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.managers.insert_one(new_manager)
    return {"message": "Manager assigned successfully", "manager_id": new_manager["id"]}

# Project Management
@api_router.get("/admin/projects")
async def get_all_projects(current_admin: User = Depends(get_current_admin)):
    """Get all projects with their details"""
    projects = await db.projects.find({}, {"_id": 0}).to_list(length=None)
    
    project_list = []
    for project in projects:
        # Get department and manager details
        department = await db.departments.find_one({"id": project["department_id"]})
        manager = await db.managers.find_one({"id": project["manager_id"]})
        
        if department and manager:
            manager_employee = await db.users.find_one({"id": manager["employee_id"]})
            
            # Get assigned employees
            assigned_employees = []
            for emp_id in project.get("employee_ids", []):
                emp = await db.users.find_one({"id": emp_id})
                if emp:
                    assigned_employees.append({
                        "id": emp["id"],
                        "name": emp["name"],
                        "email": emp["email"]
                    })
            
            project_info = {
                "id": project["id"],
                "name": project["name"],
                "description": project["description"],
                "department_id": project["department_id"],
                "department_name": department["name"],
                "manager_id": project["manager_id"],
                "manager_name": manager_employee["name"] if manager_employee else "Unknown",
                "assigned_employees": assigned_employees,
                "employee_count": len(assigned_employees),
                "start_date": project.get("start_date", ""),
                "end_date": project.get("end_date", ""),
                "status": project.get("status", "Active"),
                "created_at": project.get("created_at", "")
            }
            project_list.append(project_info)
    
    return project_list

@api_router.post("/admin/create-project")
async def create_project(project_data: ProjectCreate, current_admin: User = Depends(get_current_admin)):
    """Create a new project"""
    # Check if department and manager exist
    department = await db.departments.find_one({"id": project_data.department_id})
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    manager = await db.managers.find_one({"id": project_data.manager_id})
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    # Verify all employee IDs exist
    for emp_id in project_data.employee_ids:
        employee = await db.users.find_one({"id": emp_id, "role": "employee"})
        if not employee:
            raise HTTPException(status_code=404, detail=f"Employee {emp_id} not found")
    
    new_project = {
        "id": str(uuid.uuid4()),
        "name": project_data.name,
        "description": project_data.description,
        "department_id": project_data.department_id,
        "manager_id": project_data.manager_id,
        "employee_ids": project_data.employee_ids,
        "start_date": project_data.start_date,
        "end_date": project_data.end_date,
        "status": project_data.status,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.projects.insert_one(new_project)
    return {"message": "Project created successfully", "project_id": new_project["id"]}

# Tree Structure for Manager Assignments
@api_router.get("/admin/organization-tree")
async def get_organization_tree(current_admin: User = Depends(get_current_admin)):
    """Get complete organization tree structure"""
    # Get all data
    departments = await db.departments.find({}, {"_id": 0}).to_list(length=None)
    managers = await db.managers.find({}, {"_id": 0}).to_list(length=None)
    projects = await db.projects.find({}, {"_id": 0}).to_list(length=None)
    employees = await db.users.find({"role": "employee"}, {"_id": 0}).to_list(length=None)
    
    # Build tree structure
    tree = []
    
    for department in departments:
        dept_node = {
            "id": department["id"],
            "name": department["name"],
            "type": "department",
            "description": department.get("description", ""),
            "children": []
        }
        
        # Find managers in this department
        dept_managers = [m for m in managers if m["department_id"] == department["id"]]
        
        for manager in dept_managers:
            # Get manager employee details
            manager_employee = next((e for e in employees if e["id"] == manager["employee_id"]), None)
            if not manager_employee:
                continue
            
            manager_node = {
                "id": manager["id"],
                "name": manager_employee["name"],
                "type": "manager",
                "employee_id": manager["employee_id"],
                "email": manager_employee["email"],
                "children": []
            }
            
            # Find projects managed by this manager
            manager_projects = [p for p in projects if p["manager_id"] == manager["id"]]
            
            for project in manager_projects:
                project_employees = []
                for emp_id in project.get("employee_ids", []):
                    employee = next((e for e in employees if e["id"] == emp_id), None)
                    if employee:
                        project_employees.append({
                            "id": employee["id"],
                            "name": employee["name"],
                            "type": "employee",
                            "email": employee["email"],
                            "designation": employee.get("designation", ""),
                            "children": []
                        })
                
                project_node = {
                    "id": project["id"],
                    "name": project["name"],
                    "type": "project",
                    "description": project.get("description", ""),
                    "status": project.get("status", "Active"),
                    "start_date": project.get("start_date", ""),
                    "end_date": project.get("end_date", ""),
                    "children": project_employees
                }
                
                manager_node["children"].append(project_node)
            
            dept_node["children"].append(manager_node)
        
        tree.append(dept_node)
    
    return {
        "tree": tree,
        "summary": {
            "departments": len(departments),
            "managers": len(managers),
            "projects": len(projects),
            "employees": len(employees)
        }
    }

# Organization Settings Management
@api_router.get("/admin/organization-settings")
async def get_organization_settings(current_admin: User = Depends(get_current_admin)):
    """Get organization settings"""
    settings = await db.organization_settings.find_one({}, {"_id": 0})
    
    if not settings:
        # Return default settings if none exist
        default_settings = {
            "id": str(uuid.uuid4()),
            "company_name": "Work Hours Tracker",
            "company_logo": "",
            "establishment_date": "",
            "company_email": "",
            "founder_name": "",
            "founder_email": "",
            "address": "",
            "phone": "",
            "website": "",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.organization_settings.insert_one(default_settings)
        return default_settings
    
    return settings

@api_router.put("/admin/organization-settings")
async def update_organization_settings(settings_data: OrganizationUpdate, current_admin: User = Depends(get_current_admin)):
    """Update organization settings"""
    existing_settings = await db.organization_settings.find_one({})
    
    update_data = {
        "company_name": settings_data.company_name,
        "establishment_date": settings_data.establishment_date,
        "company_email": settings_data.company_email,
        "founder_name": settings_data.founder_name,
        "founder_email": settings_data.founder_email,
        "address": settings_data.address,
        "phone": settings_data.phone,
        "website": settings_data.website,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if existing_settings:
        await db.organization_settings.update_one(
            {"id": existing_settings["id"]}, 
            {"$set": update_data}
        )
    else:
        update_data.update({
            "id": str(uuid.uuid4()),
            "company_logo": "",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        await db.organization_settings.insert_one(update_data)
    
    return {"message": "Organization settings updated successfully"}

@api_router.post("/admin/upload-logo")
async def upload_company_logo(current_admin: User = Depends(get_current_admin)):
    """Upload company logo (placeholder for file upload)"""
    # For now, we'll use a placeholder. In production, you'd handle actual file upload
    logo_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    # Update organization settings with logo
    await db.organization_settings.update_one(
        {},
        {"$set": {"company_logo": logo_data}},
        upsert=True
    )
    
    return {"message": "Logo uploaded successfully", "logo_url": logo_data}

# Public endpoint for organization info (for login/signup screens)
@api_router.get("/organization-info")
async def get_public_organization_info():
    """Get public organization information for branding"""
    settings = await db.organization_settings.find_one({}, {"_id": 0})
    
    if not settings:
        return {
            "company_name": "Work Hours Tracker",
            "company_logo": ""
        }
    
    return {
        "company_name": settings.get("company_name", "Work Hours Tracker"),
        "company_logo": settings.get("company_logo", "")
    }

class ManagerAssignment(BaseModel):
    manager_id: str
    employee_ids: List[str]

@api_router.get("/admin/manager-assignments")
async def get_manager_assignments(current_admin: User = Depends(get_current_admin)):
    """Get all manager assignments"""
    # For now, return a simple structure. In a real system, you'd have a managers table
    employees = await db.users.find({"role": "employee"}).to_list(length=None)
    
    assignments = []
    for emp in employees:
        assignments.append({
            "employee_id": emp["id"],
            "employee_name": emp["name"],
            "employee_email": emp["email"],
            "manager_id": emp.get("manager_id", None),
            "manager_name": emp.get("manager_name", "Unassigned")
        })
    
    return {
        "total_employees": len(employees),
        "assigned_employees": len([e for e in assignments if e["manager_id"]]),
        "unassigned_employees": len([e for e in assignments if not e["manager_id"]]),
        "assignments": assignments
    }

@api_router.post("/admin/assign-manager")
async def assign_manager(assignment: ManagerAssignment, current_admin: User = Depends(get_current_admin)):
    """Assign a manager to employees"""
    # Get manager info
    manager = await db.users.find_one({"id": assignment.manager_id})
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    # Update employees with manager assignment
    for emp_id in assignment.employee_ids:
        await db.users.update_one(
            {"id": emp_id},
            {
                "$set": {
                    "manager_id": assignment.manager_id,
                    "manager_name": manager["name"]
                }
            }
        )
    
    return {"message": f"Manager {manager['name']} assigned to {len(assignment.employee_ids)} employees"}

@api_router.get("/admin/users")
async def get_all_users(current_admin: User = Depends(get_current_admin)):
    """Get all users for admin panel"""
    users = await db.users.find({"role": "employee"}).to_list(length=None)
    
    user_list = []
    for user_doc in users:
        user = User(**user_doc)
        
        # Get user's session stats
        total_sessions = await db.sessions.count_documents({"user_id": user.id, "end_time": {"$ne": None}})
        total_leaves = await db.leaves.count_documents({"user_id": user.id})
        
        # Get recent session
        recent_session = await db.sessions.find_one(
            {"user_id": user.id, "end_time": {"$ne": None}},
            sort=[("start_time", -1)]
        )
        
        user_stats = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "created_at": user.created_at.isoformat(),
            "total_sessions": total_sessions,
            "total_leaves": total_leaves,
            "last_login": recent_session["start_time"].isoformat() if recent_session else None,
            "status": "Active"
        }
        user_list.append(user_stats)
    
    return user_list

@api_router.get("/admin/dashboard-stats")
async def get_admin_dashboard_stats(current_admin: User = Depends(get_current_admin)):
    """Get admin dashboard statistics"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Total users
    total_users = await db.users.count_documents({"role": "employee"})
    
    # Active users today (users who started a session today)
    active_today = await db.sessions.count_documents({
        "start_time": {"$gte": today_start}
    })
    
    # Total sessions this month
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    sessions_this_month = await db.sessions.count_documents({
        "start_time": {"$gte": month_start},
        "end_time": {"$ne": None}
    })
    
    # Total leaves this month
    leaves_this_month = await db.leaves.count_documents({
        "date": {"$gte": month_start.date().isoformat()}
    })
    
    # Recent sessions
    recent_sessions = await db.sessions.find(
        {"end_time": {"$ne": None}},
        sort=[("start_time", -1)],
        limit=5
    ).to_list(length=5)
    
    recent_list = []
    for session in recent_sessions:
        user = await db.users.find_one({"id": session["user_id"]})
        if user:
            recent_list.append({
                "user_name": user["name"],
                "user_email": user["email"],
                "date": session["start_time"].date().isoformat(),
                "login_time": session["start_time"].strftime("%H:%M:%S"),
                "logout_time": session["end_time"].strftime("%H:%M:%S") if session.get("end_time") else None,
                "effective_hours": round(session.get("effective_seconds", 0) / 3600, 2),
                "day_type": "Half Day" if session.get("is_half_day") else "Full Day"
            })
    
    return {
        "total_users": total_users,
        "active_today": active_today,
        "sessions_this_month": sessions_this_month,
        "leaves_this_month": leaves_this_month,
        "recent_sessions": recent_list
    }

@api_router.get("/admin/user/{user_id}/sessions")
async def get_user_sessions(user_id: str, current_admin: User = Depends(get_current_admin)):
    """Get all sessions for a specific user"""
    sessions = await db.sessions.find(
        {"user_id": user_id, "end_time": {"$ne": None}},
        sort=[("start_time", -1)]
    ).to_list(length=None)
    
    session_list = []
    for session_doc in sessions:
        breaks = await db.breaks.find({"session_id": session_doc["id"]}).to_list(length=None)
        break_count = len(breaks)
        
        timesheet = await db.timesheets.find_one({"session_id": session_doc["id"]})
        
        session_list.append({
            "id": session_doc["id"],
            "date": session_doc["start_time"].date().isoformat(),
            "login_time": session_doc["start_time"].strftime("%H:%M:%S"),
            "logout_time": session_doc["end_time"].strftime("%H:%M:%S") if session_doc.get("end_time") else None,
            "effective_hours": round(session_doc.get("effective_seconds", 0) / 3600, 2),
            "break_count": break_count,
            "day_type": "Half Day" if session_doc.get("is_half_day") else "Full Day",
            "task_id": timesheet.get("task_id") if timesheet else None,
            "work_description": timesheet.get("work_description") if timesheet else None
        })
    
    return session_list

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
    total_break_seconds = 0
    for b in breaks:
        break_start = b['start_time']
        if break_start.tzinfo is None:
            break_start = break_start.replace(tzinfo=timezone.utc)
        
        break_end = b.get('end_time', now)
        if break_end and break_end.tzinfo is None:
            break_end = break_end.replace(tzinfo=timezone.utc)
        elif break_end is None:
            break_end = now
        
        total_break_seconds += (break_end - break_start).total_seconds()
    
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

# Employee Project APIs
@api_router.get("/employee/projects")
async def get_employee_projects(current_user: User = Depends(get_current_user)):
    """Get projects assigned to the current employee"""
    try:
        # Find project assignments for this employee
        assignments = await db.project_assignments.find({"employee_id": current_user.id}).to_list(length=None)
        
        projects = []
        for assignment in assignments:
            project = await db.projects.find_one({"id": assignment["project_id"]})
            if project:
                # Get manager details
                manager = await db.users.find_one({"id": project.get("manager_id")})
                manager_name = manager["name"] if manager else "Not assigned"
                
                projects.append({
                    "id": project["id"],
                    "name": project["name"],
                    "description": project.get("description", ""),
                    "status": project.get("status", "Active"),
                    "start_date": project.get("start_date", ""),
                    "end_date": project.get("end_date", ""),
                    "manager_name": manager_name,
                    "assigned_at": assignment.get("assigned_at", "").isoformat() if assignment.get("assigned_at") else ""
                })
        
        return projects
    except Exception as e:
        print(f"Error fetching employee projects: {e}")
        return []

# Leave Management APIs
@api_router.get("/employee/leave-balance")
async def get_employee_leave_balance(current_user: User = Depends(get_current_user)):
    """Get current leave balance for employee"""
    try:
        # Get leave settings
        settings = await db.leave_settings.find_one({}) or {}
        quarterly_casual = settings.get("casual_leave_quarterly", 2)
        quarterly_sick = settings.get("sick_leave_quarterly", 2) 
        quarterly_lwp = settings.get("leave_without_pay_quarterly", 5)
        
        # Calculate quarterly allocation (current quarter)
        now = datetime.now(timezone.utc)
        quarter = (now.month - 1) // 3 + 1
        
        # Get used leaves for current year
        year_start = datetime(now.year, 1, 1, tzinfo=timezone.utc)
        used_leaves = await db.leaves.find({
            "user_id": current_user.id,
            "status": "approved",
            "created_at": {"$gte": year_start}
        }).to_list(length=None)
        
        used_casual = sum(1 for leave in used_leaves if leave.get("leave_type") == "Casual Leave")
        used_sick = sum(1 for leave in used_leaves if leave.get("leave_type") == "Sick Leave") 
        used_lwp = sum(1 for leave in used_leaves if leave.get("leave_type") == "Leave without Pay")
        
        # Calculate available balance (quarters completed * quarterly allocation - used)
        available_casual = max(0, (quarter * quarterly_casual) - used_casual)
        available_sick = max(0, (quarter * quarterly_sick) - used_sick)
        available_lwp = max(0, (quarter * quarterly_lwp) - used_lwp)
        
        return {
            "casual_leave": {
                "allocated": quarter * quarterly_casual,
                "used": used_casual,
                "available": available_casual
            },
            "sick_leave": {
                "allocated": quarter * quarterly_sick,
                "used": used_sick,
                "available": available_sick
            },
            "leave_without_pay": {
                "allocated": quarter * quarterly_lwp,
                "used": used_lwp,
                "available": available_lwp
            },
            "quarter": quarter
        }
    except Exception as e:
        print(f"Error fetching leave balance: {e}")
        return {"error": "Failed to fetch leave balance"}

@api_router.post("/employee/apply-leave")
async def apply_leave(leave_data: LeaveApplicationCreate, current_user: User = Depends(get_current_user)):
    """Apply for leave"""
    try:
        # Check if user has sufficient leave balance
        balance = await get_employee_leave_balance(current_user)
        
        leave_type_key = {
            "Casual Leave": "casual_leave",
            "Sick Leave": "sick_leave", 
            "Leave without Pay": "leave_without_pay"
        }.get(leave_data.leave_type)
        
        if leave_type_key and balance[leave_type_key]["available"] < leave_data.days_count:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient {leave_data.leave_type} balance. Available: {balance[leave_type_key]['available']}"
            )
        
        # Find employee's manager
        employee = await db.employees.find_one({"email": current_user.email})
        manager_id = None
        if employee:
            dept = await db.departments.find_one({"id": employee.get("department_id")})
            if dept:
                manager_id = dept.get("manager_id")
        
        # Create leave application
        leave_application = {
            "id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "leave_type": leave_data.leave_type,
            "start_date": leave_data.start_date,
            "end_date": leave_data.end_date,
            "reason": leave_data.reason,
            "days_count": leave_data.days_count,
            "status": "pending",
            "manager_id": manager_id,
            "created_at": datetime.now(timezone.utc),
            "manager_reason": ""
        }
        
        await db.leave_applications.insert_one(leave_application)
        return {"message": "Leave application submitted successfully", "id": leave_application["id"]}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error applying leave: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply for leave")

@api_router.get("/employee/leave-requests")
async def get_employee_leave_requests(current_user: User = Depends(get_current_user)):
    """Get leave requests for current employee"""
    try:
        requests = await db.leave_applications.find(
            {"user_id": current_user.id}, 
            sort=[("created_at", -1)]
        ).to_list(length=None)
        
        formatted_requests = []
        for req in requests:
            formatted_requests.append({
                "id": req["id"],
                "leave_type": req["leave_type"],
                "start_date": req["start_date"],
                "end_date": req["end_date"],
                "reason": req["reason"],
                "days_count": req["days_count"],
                "status": req["status"],
                "created_at": req["created_at"].isoformat(),
                "manager_reason": req.get("manager_reason", "")
            })
            
        return formatted_requests
    except Exception as e:
        print(f"Error fetching leave requests: {e}")
        return []

# Manager Status Check API
@api_router.get("/employee/manager-status")
async def check_manager_status(current_user: User = Depends(get_current_user)):
    """Check if current user is a manager"""
    try:
        # Check if user is assigned as a manager in any department
        manager_assignment = await db.managers.find_one({"employee_id": current_user.id})
        
        if manager_assignment:
            # Get department details
            department = await db.departments.find_one({"id": manager_assignment.get("department_id")})
            return {
                "is_manager": True,
                "department_id": manager_assignment.get("department_id"),
                "department_name": department.get("name") if department else "Unknown Department",
                "manager_assignment_id": manager_assignment.get("id")
            }
        else:
            return {"is_manager": False}
            
    except Exception as e:
        print(f"Error checking manager status: {e}")
        return {"is_manager": False}

# Manager Leave Approval APIs  
@api_router.get("/manager/leave-requests")
async def get_pending_leave_requests(current_user: User = Depends(get_current_user)):
    """Get pending leave requests for manager approval"""
    try:
        # Find pending leave requests where current user is the manager
        requests = await db.leave_applications.find({
            "manager_id": current_user.id,
            "status": "pending"
        }, sort=[("created_at", -1)]).to_list(length=None)
        
        formatted_requests = []
        for req in requests:
            # Get employee details
            employee = await db.users.find_one({"id": req["user_id"]})
            employee_name = employee["name"] if employee else "Unknown Employee"
            
            formatted_requests.append({
                "id": req["id"],
                "employee_name": employee_name,
                "employee_id": req["user_id"],
                "leave_type": req["leave_type"],
                "start_date": req["start_date"],
                "end_date": req["end_date"],
                "reason": req["reason"],
                "days_count": req["days_count"],
                "created_at": req["created_at"].isoformat()
            })
            
        return formatted_requests
    except Exception as e:
        print(f"Error fetching manager leave requests: {e}")
        return []

@api_router.put("/manager/leave-requests/{request_id}")
async def approve_reject_leave(
    request_id: str, 
    approval_data: LeaveApprovalRequest, 
    current_user: User = Depends(get_current_user)
):
    """Approve or reject leave request"""
    try:
        # Find the leave request
        leave_request = await db.leave_applications.find_one({"id": request_id})
        if not leave_request:
            raise HTTPException(status_code=404, detail="Leave request not found")
            
        # Verify current user is the manager
        if leave_request.get("manager_id") != current_user.id:
            raise HTTPException(status_code=403, detail="You are not authorized to approve this request")
        
        # Update leave request
        update_data = {
            "status": approval_data.status,
            "manager_reason": approval_data.manager_reason,
            "approved_at": datetime.now(timezone.utc)
        }
        
        await db.leave_applications.update_one({"id": request_id}, {"$set": update_data})
        
        # If approved, create leave record
        if approval_data.status == "approved":
            leave_record = {
                "id": str(uuid.uuid4()),
                "user_id": leave_request["user_id"],
                "leave_type": leave_request["leave_type"],
                "start_date": leave_request["start_date"],
                "end_date": leave_request["end_date"],
                "days_count": leave_request["days_count"],
                "reason": leave_request["reason"],
                "status": "approved",
                "created_at": datetime.now(timezone.utc)
            }
            await db.leaves.insert_one(leave_record)
        
        # Create notification for employee
        notification_message = f"Your {leave_request['leave_type']} request from {leave_request['start_date']} to {leave_request['end_date']} has been {approval_data.status}."
        if approval_data.status == "rejected" and approval_data.manager_reason:
            notification_message += f" Reason: {approval_data.manager_reason}"
            
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": leave_request["user_id"],
            "title": f"Leave Request {approval_data.status.title()}",
            "message": notification_message,
            "type": "leave_update",
            "status": "unread",
            "created_at": datetime.now(timezone.utc),
            "related_request_id": request_id
        }
        
        await db.notifications.insert_one(notification)

        return {"message": f"Leave request {approval_data.status} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing leave approval: {e}")
        raise HTTPException(status_code=500, detail="Failed to process leave request")

# IT Ticket APIs
@api_router.post("/employee/it-tickets")
async def create_it_ticket(ticket_data: ITTicketCreate, current_user: User = Depends(get_current_user)):
    """Create new IT support ticket"""
    try:
        ticket = {
            "id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "title": ticket_data.title,
            "description": ticket_data.description,
            "category": ticket_data.category,
            "priority": ticket_data.priority,
            "status": "open",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await db.it_tickets.insert_one(ticket)
        return {"message": "IT ticket created successfully", "id": ticket["id"]}
        
    except Exception as e:
        print(f"Error creating IT ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to create IT ticket")

@api_router.get("/employee/it-tickets")
async def get_employee_tickets(current_user: User = Depends(get_current_user)):
    """Get IT tickets for current employee"""
    try:
        tickets = await db.it_tickets.find(
            {"user_id": current_user.id}, 
            sort=[("created_at", -1)]
        ).to_list(length=None)
        
        formatted_tickets = []
        for ticket in tickets:
            formatted_tickets.append({
                "id": ticket["id"],
                "title": ticket["title"],
                "description": ticket["description"],
                "category": ticket["category"],
                "priority": ticket["priority"],
                "status": ticket["status"],
                "created_at": ticket["created_at"].isoformat(),
                "updated_at": ticket.get("updated_at", ticket["created_at"]).isoformat()
            })
            
        return formatted_tickets
    except Exception as e:
        print(f"Error fetching IT tickets: {e}")
        return []

# Admin Leave Settings APIs
@api_router.get("/admin/leave-settings")
async def get_leave_settings(current_admin: User = Depends(get_current_admin)):
    """Get leave settings"""
    try:
        settings = await db.leave_settings.find_one({}) or {}
        return {
            "casual_leave_quarterly": settings.get("casual_leave_quarterly", 2),
            "sick_leave_quarterly": settings.get("sick_leave_quarterly", 2),
            "leave_without_pay_quarterly": settings.get("leave_without_pay_quarterly", 5)
        }
    except Exception as e:
        print(f"Error fetching leave settings: {e}")
        return {"error": "Failed to fetch leave settings"}

@api_router.put("/admin/leave-settings")
async def update_leave_settings(settings: LeaveSettings, current_admin: User = Depends(get_current_admin)):
    """Update leave settings"""
    try:
        # Upsert leave settings
        await db.leave_settings.replace_one(
            {}, 
            settings.dict(),
            upsert=True
        )
        return {"message": "Leave settings updated successfully"}
    except Exception as e:
        print(f"Error updating leave settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update leave settings")

# Logo Upload APIs
@api_router.post("/admin/upload-logo")
async def upload_logo(current_admin: User = Depends(get_current_admin)):
    """Upload company logo - expects form data with file"""
    from fastapi import File, UploadFile
    return {"message": "This endpoint will be updated to handle file uploads"}

@api_router.post("/admin/upload-logo-base64")
async def upload_logo_base64(
    logo_data: dict,
    current_admin: User = Depends(get_current_admin)
):
    """Upload company logo as base64"""
    try:
        import base64
        import re
        
        # Validate base64 image data
        if not logo_data.get('logo_base64'):
            raise HTTPException(status_code=400, detail="No logo data provided")
        
        logo_base64 = logo_data['logo_base64']
        
        # Check if it's a data URL and extract the base64 part
        if logo_base64.startswith('data:image'):
            # Extract base64 from data URL (data:image/png;base64,...)
            try:
                header, data = logo_base64.split(',', 1)
                logo_base64 = data
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid data URL format")
        
        # Validate base64 format
        try:
            base64.b64decode(logo_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 format")
        
        # Check file size (limit to 5MB)
        decoded_size = len(base64.b64decode(logo_base64))
        max_size = 5 * 1024 * 1024  # 5MB
        if decoded_size > max_size:
            raise HTTPException(status_code=400, detail="File size too large. Maximum 5MB allowed")
        
        # Update organization settings with the logo
        full_data_url = logo_data['logo_base64'] if logo_data['logo_base64'].startswith('data:image') else f"data:image/png;base64,{logo_base64}"
        
        # Find existing settings
        existing_settings = await db.organization_settings.find_one({})
        
        if existing_settings:
            # Update existing
            await db.organization_settings.update_one(
                {"_id": existing_settings["_id"]},
                {"$set": {"company_logo": full_data_url}}
            )
        else:
            # Create new with logo
            new_settings = {
                "id": str(uuid.uuid4()),
                "company_logo": full_data_url,
                "company_name": "Your Company",
                "establishment_date": "",
                "company_email": "",
                "founder_name": "",
                "founder_email": "",
                "address": "",
                "phone": "",
                "website": ""
            }
            await db.organization_settings.insert_one(new_settings)
        
        return {"message": "Logo uploaded successfully", "logo_url": full_data_url}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading logo: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload logo")

@api_router.delete("/admin/remove-logo")
async def remove_logo(current_admin: User = Depends(get_current_admin)):
    """Remove company logo"""
    try:
        # Find existing settings and remove logo
        existing_settings = await db.organization_settings.find_one({})
        
        if existing_settings:
            await db.organization_settings.update_one(
                {"_id": existing_settings["_id"]},
                {"$set": {"company_logo": ""}}
            )
            return {"message": "Logo removed successfully"}
        else:
            raise HTTPException(status_code=404, detail="No organization settings found")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error removing logo: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove logo")

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
    
    # Seed some sample holidays
    existing_holidays = await db.holidays.count_documents({})
    if existing_holidays == 0:
        sample_holidays = [
            {"id": str(uuid.uuid4()), "date": "2025-01-01", "name": "New Year's Day", "type": "Mandatory"},
            {"id": str(uuid.uuid4()), "date": "2025-01-26", "name": "Republic Day", "type": "Mandatory"},
            {"id": str(uuid.uuid4()), "date": "2025-03-14", "name": "Holi", "type": "Mandatory"},
            {"id": str(uuid.uuid4()), "date": "2025-08-15", "name": "Independence Day", "type": "Mandatory"},
            {"id": str(uuid.uuid4()), "date": "2025-10-02", "name": "Gandhi Jayanti", "type": "Mandatory"},
            {"id": str(uuid.uuid4()), "date": "2025-11-01", "name": "Diwali", "type": "Mandatory"},
            {"id": str(uuid.uuid4()), "date": "2025-12-25", "name": "Christmas Day", "type": "Mandatory"}
        ]
        await db.holidays.insert_many(sample_holidays)
    
    # Create default admin if none exists
    existing_admin = await db.users.find_one({"role": "admin"})
    if not existing_admin:
        default_admin = User(
            name="Admin",
            email="admin@worktracker.com",
            phone="",
            password_hash=hash_password("admin123"),
            role="admin"
        )
        await db.users.insert_one(default_admin.dict())
        print("Default admin created: admin@worktracker.com / admin123")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()