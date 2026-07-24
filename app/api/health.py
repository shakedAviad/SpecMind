from fastapi import APIRouter, HTTPException, Request

from app.models.api import HealthStatus

router = APIRouter(prefix="/health")


@router.get("/live", response_model=HealthStatus)
async def liveness() -> HealthStatus:
    return HealthStatus(status="ok")


@router.get("/ready", response_model=HealthStatus)
async def readiness(request: Request) -> HealthStatus:
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise HTTPException(status_code=503, detail="Application dependencies are not ready.")

    return HealthStatus(status="ok")
