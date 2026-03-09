from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"
    MANAGER = "MANAGER"
    BOSS = "BOSS"
    VIEWER = "VIEWER"

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER
    coffee_id: Optional[int] = None
    managed_coffee_ids: Optional[List[int]] = None
    
    receive_daily_report: bool = False
    receive_weekly_report: bool = False
    receive_monthly_report: bool = False

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    coffee_id: Optional[int] = None
    managed_coffee_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None
    receive_daily_report: Optional[bool] = None
    receive_weekly_report: Optional[bool] = None
    receive_monthly_report: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    managed_coffee_ids: List[int] = []

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Change own password: current + new."""
    current_password: str
    new_password: str = Field(..., min_length=6)


class PasswordReset(BaseModel):
    """Admin sets a user's new password (no current password required)."""
    new_password: str = Field(..., min_length=6)


# --- Coffee Schemas ---
class CoffeeBase(BaseModel):
    name: str
    location: str

class CoffeeCreate(CoffeeBase):
    ref: Optional[str] = None   # If not provided, auto-generated as CAF-XXX
    active: bool = True

class CoffeeUpdate(BaseModel):
    ref: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None
    active: Optional[bool] = None

class CoffeeResponse(CoffeeBase):
    id: int
    ref: Optional[str] = None
    active: bool

    class Config:
        from_attributes = True

# --- Question/Category Schemas ---
class AuditCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None

class AuditCategoryCreate(AuditCategoryBase):
    pass

class AuditCategoryResponse(AuditCategoryBase):
    id: int
    total_score: int = 0

    
    class Config:
        from_attributes = True

class AuditQuestionBase(BaseModel):
    text: str
    weight: int = 1
    category_id: Optional[int] = None
    correct_answer: str = "oui"
    na_score: int = 0


class AuditQuestionCreate(AuditQuestionBase):
    pass

class AuditQuestionResponse(AuditQuestionBase):
    id: int
    category: Optional[AuditCategoryResponse] = None

    class Config:
        from_attributes = True

class AuditStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

# --- Audit Schemas ---
class AuditAnswerBase(BaseModel):
    question_id: Optional[int] = None
    value: Optional[int] = None
    choice: Optional[str] = None
    comment: Optional[str] = None
    photo_data: Optional[str] = None # Base64 encoded image

class AuditAnswerCreate(AuditAnswerBase):
    pass

class AuditAnswerResponse(AuditAnswerBase):
    id: int
    photo_url: Optional[str] = None
    question: Optional[AuditQuestionResponse] = None

    class Config:
        from_attributes = True

class AuditCreate(BaseModel):
    coffee_id: int
    status: AuditStatus = AuditStatus.IN_PROGRESS
    shift: Optional[str] = None
    staff_present: Optional[str] = None
    actions_correctives: Optional[str] = None
    training_needs: Optional[str] = None
    purchases: Optional[str] = None
    photo_data: Optional[str] = None
    answers: List[AuditAnswerCreate] = []

class AuditUpdate(BaseModel):
    coffee_id: Optional[int] = None
    status: Optional[AuditStatus] = None
    score: Optional[float] = None
    shift: Optional[str] = None
    staff_present: Optional[str] = None
    actions_correctives: Optional[str] = None
    training_needs: Optional[str] = None
    purchases: Optional[str] = None
    photo_data: Optional[str] = None
    answers: Optional[List[AuditAnswerCreate]] = None

class AuditResponse(BaseModel):
    id: int
    created_at: datetime.datetime
    score: float
    status: Optional[str] = "IN_PROGRESS"
    shift: Optional[str] = None
    staff_present: Optional[str] = None
    actions_correctives: Optional[str] = None
    training_needs: Optional[str] = None
    purchases: Optional[str] = None
    photo_url: Optional[str] = None
    coffee: Optional[CoffeeResponse] = None
    auditor: Optional[UserResponse] = None
    answers: List[AuditAnswerResponse] = []

    class Config:
        from_attributes = True

# --- KPI Schemas ---
class KPIData(BaseModel):
    total_audits: int
    average_score: float
    top_performer: Optional[str]
    recent_trend: List[float] = []
    compliance_rate: float  # Percentage of audits with score >= 80
    total_coffee_shops: int
    audits_this_month: int
    average_score_this_month: float

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[int] = None

