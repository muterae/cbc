"""Teacher-facing endpoints for the CBC band playbook."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.band_playbook import BandPlaybook, get_playbook, list_playbooks

router = APIRouter(prefix="/api/v1/teacher/bands", tags=["teacher-bands"])


class BandListResponse(BaseModel):
    count: int
    bands: list[BandPlaybook]


@router.get("", response_model=BandListResponse)
def list_bands() -> BandListResponse:
    """Return every band playbook, ordered from BE to EE."""
    bands = list_playbooks()
    return BandListResponse(count=len(bands), bands=bands)


@router.get("/{band}", response_model=BandPlaybook)
def get_band(band: str) -> BandPlaybook:
    """Return one band by code (BE), full name, or slug (below-expectation)."""
    try:
        return get_playbook(band)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
