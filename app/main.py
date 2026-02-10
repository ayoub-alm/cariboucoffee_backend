from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.api.api_v1.api import api_router
from app.core.config import settings
from app.services.notification import send_weekly_report
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.models import User, UserRole, Coffee, AuditCategory, AuditQuestion
from app.core.security import get_password_hash
from app.db.seed_data import DEFAULT_ADMIN, DEFAULT_COFFEES, AUDIT_CATEGORIES_DATA
from sqlalchemy import select

app = FastAPI(title=settings.PROJECT_NAME)

# Set all CORS enabled origins - Always enable for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins like ["http://localhost:4200"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
                    description=cat_data["description"]
                )
                db.add(category)
                await db.flush()  # Get the category ID
                
                for question_data in cat_data["questions"]:
                    question = AuditQuestion(
                        text=question_data["text"],
                        weight=question_data["weight"],
                        category_id=category.id
                    )
                    db.add(question)
            
            await db.commit()
            print(f"Seeded {len(AUDIT_CATEGORIES_DATA)} audit categories with questions")

    # Start the scheduler
    scheduler.add_job(send_weekly_report, "interval", weeks=1) # Run weekly
    scheduler.start()
    print("Scheduler started!")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

@app.get("/")
def root():
    return {"message": "Welcome to Caribou Coffee API"}
