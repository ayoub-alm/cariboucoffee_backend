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
    CONTROLLER = "CONTROLLER"

# --- Bulk Actions ---
class BulkDelete(BaseModel):
    ids: List[int]

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
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None

class CoffeeCreate(CoffeeBase):
    ref: Optional[str] = None   # If not provided, auto-generated as CAF-XXX
    active: bool = True

class CoffeeUpdate(BaseModel):
    ref: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None
    active: Optional[bool] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None

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
    display_order: int = 0

class AuditCategoryCreate(AuditCategoryBase):
    pass

class AuditCategoryResponse(AuditCategoryBase):
    id: int
    total_score: int = 0
    display_order: int = 0

    class Config:
        from_attributes = True

class AuditQuestionBase(BaseModel):
    text: str
    weight: int = 1
    category_id: Optional[int] = None
    correct_answer: str = "oui"
    na_score: int = 0
    display_order: int = 0

class AuditQuestionCreate(AuditQuestionBase):
    pass

class AuditQuestionResponse(AuditQuestionBase):
    id: int
    display_order: int = 0
    category: Optional[AuditCategoryResponse] = None

    class Config:
        from_attributes = True


# --- Reorder Schemas ---
class ReorderItem(BaseModel):
    id: int
    display_order: int

class ReorderRequest(BaseModel):
    items: List[ReorderItem]

class AuditStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

# --- Audit Schemas ---
class AuditAnswerBase(BaseModel):
    question_id: Optional[int] = None
    value: Optional[int] = None
    choice: Optional[str] = None
    comment: Optional[str] = None
    photo_data: Optional[List[str]] = None

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
    date: Optional[datetime.datetime] = None
    status: AuditStatus = AuditStatus.IN_PROGRESS
    shift: Optional[str] = None
    staff_present: Optional[str] = None
    actions_correctives: Optional[str] = None
    training_needs: Optional[str] = None
    purchases: Optional[str] = None
    conclusion: Optional[str] = None
    photo_data: Optional[List[str]] = None
    existing_photo_urls: Optional[List[str]] = None
    answers: List[AuditAnswerCreate] = []

class AuditUpdate(BaseModel):
    coffee_id: Optional[int] = None
    date: Optional[datetime.datetime] = None
    status: Optional[AuditStatus] = None
    score: Optional[float] = None
    shift: Optional[str] = None
    staff_present: Optional[str] = None
    actions_correctives: Optional[str] = None
    training_needs: Optional[str] = None
    purchases: Optional[str] = None
    conclusion: Optional[str] = None
    photo_data: Optional[List[str]] = None
    existing_photo_urls: Optional[List[str]] = None
    answers: Optional[List[AuditAnswerCreate]] = None

class AuditResponse(BaseModel):
    id: int
    created_at: datetime.datetime
    date: Optional[datetime.datetime] = None
    score: float
    status: Optional[str] = "IN_PROGRESS"
    shift: Optional[str] = None
    staff_present: Optional[str] = None
    actions_correctives: Optional[str] = None
    training_needs: Optional[str] = None
    purchases: Optional[str] = None
    conclusion: Optional[str] = None
    photo_url: Optional[str] = None
    coffee: Optional[CoffeeResponse] = None
    auditor: Optional[UserResponse] = None
    answers: List[AuditAnswerResponse] = []

    class Config:
        from_attributes = True

class AuditListResponse(BaseModel):
    """Paginated wrapper returned by GET /audits."""
    items: List[AuditResponse]
    total: int
    page: int
    size: int
    pages: int
    average_score: float = 0.0

# --- KPI Schemas ---
class KPIData(BaseModel):
    total_audits: int
    average_score: float
    top_performer: Optional[str]
    worst_performer: Optional[str] = None
    recent_trend: List[float] = []
    scores_per_category: dict[str, float] = {}
    compliance_rate: float  # Percentage of audits with score >= 80
    total_coffee_shops: int
    audits_this_month: int
    average_score_this_month: float
    timing_scores: dict[str, float] = {}  # Coffee name -> timing score (%)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[int] = None


# --- User Rights Schemas ---
class ModulePermissions(BaseModel):
    read:   Optional[bool] = None
    create: Optional[bool] = None
    update: Optional[bool] = None
    delete: Optional[bool] = None


class UserRightsUpdate(BaseModel):
    coffees:    Optional[ModulePermissions] = None
    audits:     Optional[ModulePermissions] = None
    users:      Optional[ModulePermissions] = None
    categories: Optional[ModulePermissions] = None
    questions:  Optional[ModulePermissions] = None

# --- Conformity Threshold Schemas ---
class ConformityThresholdBase(BaseModel):
    conforme_min: float = Field(90.0, ge=1.0)
    partiel_min: float = Field(70.0, ge=1.0)

class ConformityThresholdUpdate(BaseModel):
    conforme_min: Optional[float] = Field(None, ge=1.0)
    partiel_min: Optional[float] = Field(None, ge=1.0)

class ConformityThresholdResponse(ConformityThresholdBase):
    id: int
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Daily Time Record Schemas ---
class DailyTimeRecordBase(BaseModel):
    date: datetime.date
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None

class DailyTimeRecordCreate(DailyTimeRecordBase):
    coffee_id: int

class DailyTimeRecordUpdate(BaseModel):
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None

class DailyTimeRecordResponse(DailyTimeRecordBase):
    id: int
    coffee_id: int
    controller_id: int

    class Config:
        from_attributes = True


# --- Schedule Threshold Schemas ---
class ScheduleThresholdBase(BaseModel):
    green_min:  float = Field(100.0, ge=1.0, le=100.0)
    orange_min: float = Field(90.0,  ge=1.0, le=100.0)

class ScheduleThresholdUpdate(BaseModel):
    green_min:  Optional[float] = Field(None, ge=1.0, le=100.0)
    orange_min: Optional[float] = Field(None, ge=1.0, le=100.0)

class ScheduleThresholdResponse(ScheduleThresholdBase):
    id: int
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Enriched Daily Time Record (with backend-computed score) ---
class DailyTimeRecordEnriched(DailyTimeRecordBase):
    id: int
    coffee_id: int
    controller_id: int
    score: float                  # computed by backend
    status: str                   # "green" | "orange" | "red"

    class Config:
        from_attributes = True


# --- Paginated wrapper for GET /daily-logs ---
class DailyLogListResponse(BaseModel):
    items: List[DailyTimeRecordEnriched]
    total: int
    page: int
    size: int
    pages: int
    # Pre-computed KPI stats (over ALL filtered records, not just current page)
    average_score: float = 0.0
    late_openings: int = 0
    early_closures: int = 0
    monthly_average: float = 0.0
    weekly_average: float = 0.0
