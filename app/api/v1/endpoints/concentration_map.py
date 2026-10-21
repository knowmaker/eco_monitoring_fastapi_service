from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.concentration_map import (
    ConcentrationMapResponse,
    ConcentrationMapSubstancesResponse,
    ConcentrationMapTimelineResponse,
    ConcentrationMapValueResponse,
)
from app.services.concentration_frame import render_stored_tile
from app.services.concentration_map import (
    get_concentration_map_frame,
    get_concentration_map_substances,
    get_concentration_map_timeline,
    get_concentration_map_value,
)


router = APIRouter(prefix="/concentration-map", tags=["concentration-map"])


@router.get("/substances", response_model=ConcentrationMapSubstancesResponse)
def concentration_map_substances(
    db: Session = Depends(get_db),
) -> ConcentrationMapSubstancesResponse:
    return get_concentration_map_substances(db)


@router.get("/timeline", response_model=ConcentrationMapTimelineResponse)
def concentration_map_timeline(
    substance_code: str = Query(..., min_length=1, max_length=20),
    past_hours: int = Query(24, ge=1, le=24 * 366),
    future_hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
) -> ConcentrationMapTimelineResponse:
    return get_concentration_map_timeline(db, substance_code.upper(), past_hours, future_hours)


@router.get("/value", response_model=ConcentrationMapValueResponse)
def concentration_map_value(
    substance_code: str = Query(..., min_length=1, max_length=20),
    hour_start: datetime = Query(...),
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    db: Session = Depends(get_db),
) -> ConcentrationMapValueResponse:
    result = get_concentration_map_value(
        db,
        substance_code.upper(),
        hour_start,
        latitude,
        longitude,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Concentration frame not found")
    return result


@router.get("/tiles/{frame_id}/{content_sha256}/{zoom}/{tile_x}/{tile_y}.png")
def concentration_map_tile(
    frame_id: int,
    content_sha256: str,
    zoom: int,
    tile_x: int,
    tile_y: int,
) -> Response:
    tile_limit = 2**zoom if 0 <= zoom <= 22 else 0
    if tile_x < 0 or tile_y < 0 or tile_x >= tile_limit or tile_y >= tile_limit:
        raise HTTPException(status_code=404, detail="Tile not found")
    try:
        image = render_stored_tile(
            frame_id,
            content_sha256,
            zoom,
            tile_x,
            tile_y,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Concentration frame not found")

    return Response(
        content=image,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.get("", response_model=ConcentrationMapResponse)
def concentration_map(
    substance_code: str = Query(..., min_length=1, max_length=20),
    hour_start: datetime = Query(...),
    db: Session = Depends(get_db),
) -> ConcentrationMapResponse:
    return get_concentration_map_frame(db, substance_code.upper(), hour_start)
