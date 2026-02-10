from fastapi import APIRouter
from app.api.api_v1.endpoints import auth, audits, kpi, users, coffees, categories, questions

api_router = APIRouter()
api_router.include_router(auth.router, tags=["login"])
api_router.include_router(audits.router, prefix="/audits", tags=["audits"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(questions.router, prefix="/questions", tags=["questions"])
api_router.include_router(coffees.router, prefix="/coffees", tags=["coffees"])
api_router.include_router(kpi.router, prefix="/kpi", tags=["kpi"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
