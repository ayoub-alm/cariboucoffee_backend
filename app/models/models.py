import enum
from sqlalchemy import BigInteger, Column, Date, DateTime, Float, ForeignKey, Integer, String, Enum, Boolean, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"
    MANAGER = "MANAGER"
    BOSS = "BOSS"
    VIEWER = "VIEWER"

manager_coffees = Table(
    "manager_coffees",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("coffee_id", Integer, ForeignKey("coffees.id"), primary_key=True),
)

class Coffee(Base):
    __tablename__ = "coffees"
    
    id = Column(Integer, primary_key=True, index=True)
    ref = Column(String, unique=True, nullable=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    active = Column(Boolean, default=True)

    audits = relationship("Audit", back_populates="coffee")
    viewers = relationship("User", back_populates="assigned_coffee", foreign_keys="User.coffee_id")
    managers = relationship("User", secondary=manager_coffees, back_populates="managed_coffees")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.VIEWER)
    
    receive_daily_report = Column(Boolean, default=False)
    receive_weekly_report = Column(Boolean, default=False)
    receive_monthly_report = Column(Boolean, default=False)
    
    # For VIEWER: single assigned coffee
    coffee_id = Column(Integer, ForeignKey("coffees.id"), nullable=True)
    assigned_coffee = relationship("Coffee", back_populates="viewers", foreign_keys=[coffee_id])
    
    # For MANAGER: multiple managed coffees
    managed_coffees = relationship("Coffee", secondary=manager_coffees, back_populates="managers")
    
    audits_created = relationship("Audit", back_populates="auditor")
    rights = relationship("UserRights", back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserRights(Base):
    __tablename__ = "user_rights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Coffees module
    coffees_read   = Column(Boolean, default=False)
    coffees_create = Column(Boolean, default=False)
    coffees_update = Column(Boolean, default=False)
    coffees_delete = Column(Boolean, default=False)

    # Audits module
    audits_read   = Column(Boolean, default=False)
    audits_create = Column(Boolean, default=False)
    audits_update = Column(Boolean, default=False)
    audits_delete = Column(Boolean, default=False)

    # Users module
    users_read   = Column(Boolean, default=False)
    users_create = Column(Boolean, default=False)
    users_update = Column(Boolean, default=False)
    users_delete = Column(Boolean, default=False)

    # Categories module
    categories_read   = Column(Boolean, default=False)
    categories_create = Column(Boolean, default=False)
    categories_update = Column(Boolean, default=False)
    categories_delete = Column(Boolean, default=False)

    # Questions module
    questions_read   = Column(Boolean, default=False)
    questions_create = Column(Boolean, default=False)
    questions_update = Column(Boolean, default=False)
    questions_delete = Column(Boolean, default=False)

    user = relationship("User", back_populates="rights")


class AuditCategory(Base):
    __tablename__ = "audit_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    
    questions = relationship("AuditQuestion", back_populates="category", order_by="AuditQuestion.display_order")

    @property
    def total_score(self) -> int:
        return sum(q.weight for q in self.questions) if self.questions else 0


class AuditQuestion(Base):
    __tablename__ = "audit_questions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    weight = Column(Integer, default=1)
    display_order = Column(Integer, default=0, nullable=False)

    category_id = Column(Integer, ForeignKey("audit_categories.id"))
    
    category = relationship("AuditCategory", back_populates="questions")
    answers = relationship("AuditAnswer", back_populates="question")
    
    correct_answer = Column(String, default="oui")
    na_score = Column(Integer, default=0)


class AuditStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class Audit(Base):
    __tablename__ = "audits"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    score = Column(Float, default=0.0)
    status = Column(Enum(AuditStatus), default=AuditStatus.IN_PROGRESS)
    
    coffee_id = Column(Integer, ForeignKey("coffees.id"))
    auditor_id = Column(Integer, ForeignKey("users.id"))
    
    # User-selected audit date/time
    date = Column(DateTime(timezone=True), nullable=True)
    
    # Extra info
    shift = Column(String, nullable=True)
    staff_present = Column(String, nullable=True)
    actions_correctives = Column(String, nullable=True)
    training_needs = Column(String, nullable=True)
    purchases = Column(String, nullable=True)
    conclusion = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    
    coffee = relationship("Coffee", back_populates="audits")
    auditor = relationship("User", back_populates="audits_created")
    answers = relationship("AuditAnswer", back_populates="audit", cascade="all, delete-orphan")

class AuditAnswer(Base):
    __tablename__ = "audit_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    value = Column(Integer) # e.g. 0-5
    choice = Column(String, nullable=True) # 'oui', 'non', 'n/a'
    comment = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)

    
    audit_id = Column(Integer, ForeignKey("audits.id"))
    question_id = Column(Integer, ForeignKey("audit_questions.id"))
    
    audit = relationship("Audit", back_populates="answers")
    question = relationship("AuditQuestion", back_populates="answers")

class ConformityThreshold(Base):
    __tablename__ = "conformity_thresholds"
    
    id = Column(Integer, primary_key=True, index=True)
    conforme_min = Column(Float, default=90.0)
    partiel_min = Column(Float, default=70.0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
