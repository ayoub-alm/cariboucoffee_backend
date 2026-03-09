from fastapi import APIRouter, Depends, HTTPException
from app.api import deps
from app.models.models import User, UserRole
from app.services.notification import send_weekly_report

router = APIRouter()

@router.post("/send-now", status_code=200)
async def trigger_email_now(
    current_user: User = Depends(deps.get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    try:
        await send_weekly_report()
        return {"success": True, "message": "Emails sent successfully."}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
