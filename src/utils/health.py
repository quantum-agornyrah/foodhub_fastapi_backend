from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.utils.db import get_db
import time

router = APIRouter()

# Liveness: "is the process running at all?"
# If this fails → restart the container
@router.get("/health/live")
async def liveness():
     return {"status": "alive", "timestamp": time.time()}

# Readiness: "is the app ready to serve traffic?"
# If this fails → stop sending traffic here (but don't restart)
@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    checks = {}

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    # Overall status
    all_ok = all(v == "ok" for v in checks.values())
    status_code = 200 if all_ok else 503

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if all_ok else "degraded", "checks": checks}
    )
