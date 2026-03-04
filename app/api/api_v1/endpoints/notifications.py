from fastapi import APIRouter, HTTPException
from app.services.notification import send_weekly_report

router = APIRouter()

@router.post("/send-now", status_code=200)
async def trigger_email_now():
    """
    Manually triggers the weekly report email to all subscribed users.
    """
    try:
        await send_weekly_report()
        return {"success": True, "message": "Emails sent successfully."}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
