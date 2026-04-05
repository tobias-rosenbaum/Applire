from fastapi import APIRouter
from pydantic import BaseModel

from apliqa import __version__
from applire.config import HAS_CLOUD

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    edition: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        edition="cloud" if HAS_CLOUD else "community",
        version=__version__,
    )
