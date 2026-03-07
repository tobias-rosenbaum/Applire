from fastapi import APIRouter
from pydantic import BaseModel

from apliqa.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    edition: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", edition=settings.apliqa_edition)
