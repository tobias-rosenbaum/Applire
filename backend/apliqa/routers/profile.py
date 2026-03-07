import asyncio
import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from apliqa.db.session import get_db
from apliqa.providers.mistral import MistralProvider
from apliqa.schemas.profile import LinkedInImportRequest, MasterProfileResponse
from apliqa.services.profile import (
    get_profile,
    import_from_linkedin,
    import_from_pdf,
    patch_profile_section,
)

router = APIRouter(prefix="/api/profile", tags=["profile"])

_LLM_TIMEOUT_SECONDS = 60.0


def _get_provider() -> MistralProvider:
    return MistralProvider()


@router.post("/import", response_model=MasterProfileResponse, status_code=status.HTTP_200_OK)
async def import_profile(
    db: AsyncSession = Depends(get_db),
    provider: MistralProvider = Depends(_get_provider),
    file: Annotated[UploadFile | None, File(description="CV as PDF")] = None,
    linkedin_json: Annotated[str | None, Form(description="LinkedIn export JSON string")] = None,
) -> MasterProfileResponse:
    if file is None and linkedin_json is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide either a PDF file or linkedin_json",
        )
    if file is not None and linkedin_json is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide either a PDF file or linkedin_json, not both",
        )

    try:
        if file is not None:
            if not file.filename or not file.filename.lower().endswith(".pdf"):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Uploaded file must be a PDF",
                )
            file_bytes = await file.read()
            coro = import_from_pdf(file_bytes, db, provider)
        else:
            try:
                parsed = json.loads(linkedin_json)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="linkedin_json is not valid JSON",
                )
            coro = import_from_linkedin(parsed, db, provider)

        return await asyncio.wait_for(coro, timeout=_LLM_TIMEOUT_SECONDS)

    except HTTPException:
        raise
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="LLM request timed out",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM returned invalid JSON",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("", response_model=MasterProfileResponse, status_code=status.HTTP_200_OK)
async def get_current_profile(
    db: AsyncSession = Depends(get_db),
) -> MasterProfileResponse:
    profile = await get_profile(db)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile found. Import a CV first.",
        )
    return profile


@router.patch("/{section}", response_model=MasterProfileResponse, status_code=status.HTTP_200_OK)
async def patch_section(
    section: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MasterProfileResponse:
    body = await request.json()
    try:
        return await patch_profile_section(section, body, db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
