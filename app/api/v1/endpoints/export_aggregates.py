from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.export_aggregates import ExportAggregatesRequest
from app.services.export_aggregates import build_aggregates_export


XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/aggregates")
def export_aggregates(
    payload: ExportAggregatesRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Response:
    export_file = build_aggregates_export(db, payload)
    headers = {
        "Content-Disposition": f"attachment; filename={export_file.filename}; filename*=UTF-8''{export_file.filename}",
    }
    return Response(content=export_file.content, media_type=XLSX_MEDIA_TYPE, headers=headers)
