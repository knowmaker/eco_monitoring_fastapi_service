from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.query_params import parse_month_query
from app.core.dates import current_local_date
from app.db.session import get_db
from app.schemas.profile_state import ProfileStateHourlyResponse, ProfileStateMonthlyResponse
from app.services.profile_readings import get_hourly_profiles, get_monthly_profiles


router = APIRouter(prefix="/profile-state", tags=["profile-state"])


@router.get("/hourly", response_model=ProfileStateHourlyResponse)
def get_hourly_profile_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_date: date | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
) -> ProfileStateHourlyResponse:
    day = target_date or current_local_date()
    profiles = get_hourly_profiles(db, monitoring_post_id, day)
    return ProfileStateHourlyResponse(date=day.isoformat(), profiles=profiles)


@router.get("/monthly", response_model=ProfileStateMonthlyResponse)
def get_monthly_profile_state(
    monitoring_post_id: int = Query(..., ge=1),
    target_month: str | None = Query(None, alias="month"),
    db: Session = Depends(get_db),
) -> ProfileStateMonthlyResponse:
    period = parse_month_query(target_month)
    profiles = get_monthly_profiles(db, monitoring_post_id, period.year, period.month, period.days_count)
    return ProfileStateMonthlyResponse(month=period.key, profiles=profiles)
