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
    """Get calendar data for a specific month"""
    from calendar import monthrange
    import calendar as cal
    
    # Get first and last day of the month
    first_day = datetime(year, month, 1, tzinfo=timezone.utc)
    last_day_num = monthrange(year, month)[1]
    last_day = datetime(year, month, last_day_num, 23, 59, 59, tzinfo=timezone.utc)
    
    # Get all sessions for the month
    sessions = await db.sessions.find({
        "user_id": current_user.id,
        "start_time": {"$gte": first_day, "$lte": last_day},
        "end_time": {"$ne": None}
    }).to_list(length=None)
    
    # Get all leaves for the month
    leaves = await db.leaves.find({
        "user_id": current_user.id,
        "date": {
            "$gte": first_day.date().isoformat(),
            "$lte": last_day.date().isoformat()
        }
    }).to_list(length=None)
    
    # Get holidays for the month
    holidays = await db.holidays.find({
        "date": {
            "$gte": first_day.date().isoformat(),
            "$lte": last_day.date().isoformat()
        }
    }).to_list(length=None)
    
    # Build calendar data
    calendar_days = []
    for day in range(1, last_day_num + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        
        # Check what type of day this is
        day_type = None
        
        # Check if it's a holiday
        if any(h["date"] == date_str for h in holidays):
            day_type = "holiday"
        
        # Check if user worked
        elif any(s["start_time"].date().isoformat() == date_str for s in sessions):
            session = next(s for s in sessions if s["start_time"].date().isoformat() == date_str)
            day_type = "half-day" if session.get("is_half_day") else "worked"
        
        # Check if user was on leave
        elif any(l["date"] == date_str for l in leaves):
            leave = next(l for l in leaves if l["date"] == date_str)
            day_type = "half-day" if leave["type"] == "half" else "leave"
        
        calendar_days.append({
            "date": date_str,
            "day": day,
            "type": day_type,
            "weekday": cal.weekday(year, month, day)
        })
    
    return {
        "year": year,
        "month": month,
        "days": calendar_days
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
    holidays = await db.holidays.find({}).sort("date", 1).to_list(length=None)
    
    return {
        "total_holidays": len(holidays),
        "holidays_this_year": len([h for h in holidays if h["date"].startswith(str(current_year))]),
        "holidays": holidays
    }

@api_router.post("/admin/add-holiday")
async def add_holiday(holiday_data: dict, current_admin: User = Depends(get_current_admin)):
    """Add a new holiday"""
    new_holiday = {
        "id": str(uuid.uuid4()),
        "date": holiday_data["date"],
        "name": holiday_data["name"]
    }
    
    # Check if holiday already exists for this date
    existing = await db.holidays.find_one({"date": holiday_data["date"]})
    if existing:
        raise HTTPException(status_code=400, detail="Holiday already exists for this date")
    
    await db.holidays.insert_one(new_holiday)
    return {"message": "Holiday added successfully", "holiday_id": new_holiday["id"]}

@api_router.delete("/admin/holiday/{holiday_id}")
async def delete_holiday(holiday_id: str, current_admin: User = Depends(get_current_admin)):
    """Delete a holiday"""
    result = await db.holidays.delete_one({"id": holiday_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Holiday not found")
    
    return {"message": "Holiday deleted successfully"}

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
            {"id": str(uuid.uuid4()), "date": "2025-01-01", "name": "New Year's Day"},
            {"id": str(uuid.uuid4()), "date": "2025-01-26", "name": "Republic Day"},
            {"id": str(uuid.uuid4()), "date": "2025-03-14", "name": "Holi"},
            {"id": str(uuid.uuid4()), "date": "2025-08-15", "name": "Independence Day"},
            {"id": str(uuid.uuid4()), "date": "2025-10-02", "name": "Gandhi Jayanti"},
            {"id": str(uuid.uuid4()), "date": "2025-11-01", "name": "Diwali"},
            {"id": str(uuid.uuid4()), "date": "2025-12-25", "name": "Christmas Day"}
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