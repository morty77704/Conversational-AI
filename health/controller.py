from fastapi import APIRouter

from health.entity import HealthResponse


health_router = APIRouter()


@health_router.get("/live", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return HealthResponse(status="ok")