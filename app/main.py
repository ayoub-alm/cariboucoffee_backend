from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.api.api_v1.api import api_router
from app.core.config import settings
from app.services.notification import send_weekly_report, send_daily_report, send_monthly_report
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.models import User, UserRole, Coffee, AuditCategory, AuditQuestion
from app.core.security import get_password_hash
from app.db.seed_data import DEFAULT_ADMIN, DEFAULT_COFFEES, AUDIT_CATEGORIES_DATA
from sqlalchemy import select, func
import os
import logging

# Setup basic logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME)

# Set all CORS enabled origins - Always enable for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins like ["http://localhost:4200"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directory exists
os.makedirs("app/static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# Also mount at /api/static to handle cases where Apache proxies /api to the backend without stripping the prefix
app.mount("/api/static", StaticFiles(directory="app/static"), name="api_static")

app.include_router(api_router, prefix=settings.API_V1_STR)

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed database
    async with SessionLocal() as db:
        # Seed Admin User
        result = await db.execute(select(User).where(User.role == UserRole.ADMIN))
        admin = result.scalars().first()
        if not admin:
            admin_user = User(
                email=DEFAULT_ADMIN["email"],
                hashed_password=get_password_hash(DEFAULT_ADMIN["password"]),
                full_name=DEFAULT_ADMIN["full_name"],
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)
            await db.commit()
            print(f"Admin user created: {DEFAULT_ADMIN['email']} / {DEFAULT_ADMIN['password']}")
        
        # Seed Coffee Shops
        result = await db.execute(select(Coffee))
        coffees = result.scalars().all()
        if not coffees:
            for coffee_data in DEFAULT_COFFEES:
                coffee = Coffee(**coffee_data)
                db.add(coffee)
            await db.commit()
            print(f"Seeded {len(DEFAULT_COFFEES)} coffee shops")
        
        # Seed Audit Categories and Questions
        result = await db.execute(select(AuditCategory))
        categories = result.scalars().all()
        if not categories:
            for cat_name, cat_data in AUDIT_CATEGORIES_DATA.items():
                category = AuditCategory(
                    name=cat_name,
                    description=cat_data.get("description"),
                    icon=cat_data.get("icon")
                )
                db.add(category)
                await db.flush()
                
                for question_data in cat_data["questions"]:
                    question = AuditQuestion(
                        text=question_data["text"],
                        weight=question_data.get("weight", 1),
                        category_id=category.id,
                        correct_answer=question_data.get("correct_answer", "oui")
                    )
                    db.add(question)
            
            await db.commit()
            print(f"Seeded {len(AUDIT_CATEGORIES_DATA)} audit categories with questions")

        # Seed test audits & daily logs for last 3 months (100 audits, 400 logs)
        from app.models.models import Audit, DailyTimeRecord, AuditStatus
        from datetime import date, timedelta, datetime
        import random

        audit_count_res = await db.execute(select(func.count(Audit.id)))
        audit_count = audit_count_res.scalar() or 0

        log_count_res = await db.execute(select(func.count(DailyTimeRecord.id)))
        log_count = log_count_res.scalar() or 0

        if audit_count == 0 and log_count == 0:
            print("Seeding 100 audits and 400 daily logs for the last 3 months...")
            admin_user = (await db.execute(select(User).where(User.role == UserRole.ADMIN))).scalars().first()
            coffees = (await db.execute(select(Coffee))).scalars().all()
            
            if admin_user and coffees:
                # 1. Seed 400 Daily Time Records (100 days per café)
                today = date.today()
                for i in range(100):
                    log_date = today - timedelta(days=i)
                    for coffee in coffees:
                        exp_open_h = 7
                        exp_close_h = 22
                        if coffee.opening_time:
                            try: exp_open_h = int(coffee.opening_time.split(":")[0])
                            except: pass
                        if coffee.closing_time:
                            try: exp_close_h = int(coffee.closing_time.split(":")[0])
                            except: pass
                        
                        r = random.random()
                        if r < 0.80:
                            opening = f"{exp_open_h:02d}:00"
                            closing = f"{exp_close_h:02d}:00"
                        elif r < 0.95:
                            opening = f"{exp_open_h:02d}:{random.choice([15, 30])}"
                            closing = f"{exp_close_h - 1:02d}:{random.choice([30, 45])}"
                        else:
                            opening = f"{exp_open_h + random.choice([1, 2]):02d}:{random.choice([0, 15, 30])}"
                            closing = f"{exp_close_h - random.choice([2, 3]):02d}:{random.choice([0, 30])}"
                        
                        log_rec = DailyTimeRecord(
                            date=log_date,
                            opening_time=opening,
                            closing_time=closing,
                            coffee_id=coffee.id,
                            controller_id=admin_user.id
                        )
                        db.add(log_rec)
                
                # 2. Seed 100 Audits distributed randomly over last 90 days
                audit_dates = [datetime.now() - timedelta(days=random.randint(0, 90)) for _ in range(100)]
                for dt in audit_dates:
                    coffee = random.choice(coffees)
                    r = random.random()
                    if r < 0.70:
                        score = random.uniform(82.0, 98.0)
                    elif r < 0.90:
                        score = random.uniform(70.0, 79.9)
                    else:
                        score = random.uniform(45.0, 69.9)
                    
                    audit = Audit(
                        date=dt,
                        created_at=dt,
                        score=round(score, 1),
                        status=AuditStatus.COMPLETED,
                        coffee_id=coffee.id,
                        auditor_id=admin_user.id
                    )
                    db.add(audit)
                
                await db.commit()
                print("Seeded database with 100 test audits and 400 daily logs successfully!")

    # Logging for scheduler
    cron_logger = logging.getLogger("apscheduler")
    cron_handler = logging.FileHandler("cron_jobs.log")
    cron_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    cron_logger.addHandler(cron_handler)

    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

    def job_listener(event):
        if event.exception:
            cron_logger.error(f"Job {event.job_id} FAILED: {event.exception}")
        else:
            cron_logger.info(f"Job {event.job_id} completed successfully.")

    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    # Schedule automated reports
    # Daily: Every day at 08:00
    scheduler.add_job(send_daily_report, "cron", hour=8, minute=0, id="daily_report")
    
    # Weekly: Every Monday at 08:30
    scheduler.add_job(send_weekly_report, "cron", day_of_week="mon", hour=8, minute=30, id="weekly_report")
    
    # Monthly: 1st of every month at 09:00
    scheduler.add_job(send_monthly_report, "cron", day=1, hour=9, minute=0, id="monthly_report")
    
    scheduler.start()
    print("Scheduler started!")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

@app.get("/")
def root():
    return {"message": "Welcome to Caribou Coffee API"}
