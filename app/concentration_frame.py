from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from io import BytesIO
from math import atan, cos, degrees, log, pi, radians, sinh, tan

import numpy as np
from PIL import Image, ImageDraw
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.gas_concentration_frame import GasConcentrationFrame


TILE_SIZE = 256
COLOR_STOPS = (
    (0.0, (26, 152, 80)),
    (0.25, (145, 207, 96)),
    (0.4, (255, 224, 102)),
    (0.75, (255, 213, 79)),
    (0.9, (245, 124, 0)),
    (1.0, (215, 48, 39)),
)
ALPHA_STOPS = ((0.0, 0.0), (0.2, 0.18), (0.6, 0.55), (1.0, 0.78))


@dataclass(frozen=True)
class ConcentrationFrameData:
    south: np.ndarray
    west: np.ndarray
    north: np.ndarray
    east: np.ndarray
    value: np.ndarray
    confidence: np.ndarray


@lru_cache(maxsize=16)
def load_frame(frame_id: int, content_sha256: str) -> ConcentrationFrameData:
    with SessionLocal() as db:
        content = db.scalar(
            select(GasConcentrationFrame.payload).where(
                GasConcentrationFrame.id == frame_id,
                GasConcentrationFrame.content_sha256 == content_sha256,
            )
        )
    if content is None:
        raise ValueError("Concentration frame not found")
    content = bytes(content)
    if sha256(content).hexdigest() != content_sha256:
        raise ValueError("Concentration frame checksum does not match metadata")
    with np.load(BytesIO(content), allow_pickle=False) as archive:
        version = int(archive["format_version"])
        if version != 1:
            raise ValueError(f"Unsupported concentration frame format: {version}")
        return ConcentrationFrameData(
            south=archive["south"].astype(float),
            west=archive["west"].astype(float),
            north=archive["north"].astype(float),
            east=archive["east"].astype(float),
            value=archive["value"].astype(float),
            confidence=archive["confidence"].astype(float),
        )


def _interpolate(stops: tuple, value: float):
    value = min(max(value, 0.0), 1.0)
    for (left_at, left_value), (right_at, right_value) in zip(stops, stops[1:]):
        if value <= right_at:
            ratio = (value - left_at) / (right_at - left_at)
            if isinstance(left_value, tuple):
                return tuple(
                    round(left + (right - left) * ratio)
                    for left, right in zip(left_value, right_value)
                )
            return left_value + (right_value - left_value) * ratio
    return stops[-1][1]


def _tile_bounds(zoom: int, x: int, y: int) -> tuple[float, float, float, float]:
    scale = 2**zoom
    west = x / scale * 360.0 - 180.0
    east = (x + 1) / scale * 360.0 - 180.0
    north = degrees(atan(sinh(pi * (1.0 - 2.0 * y / scale))))
    south = degrees(atan(sinh(pi * (1.0 - 2.0 * (y + 1) / scale))))
    return south, west, north, east


def _tile_pixel_y(latitude: float, zoom: int, tile_y: int) -> float:
    latitude = min(max(latitude, -85.05112878), 85.05112878)
    angle = radians(latitude)
    world_y = (1.0 - log(tan(angle) + 1.0 / cos(angle)) / pi) / 2.0 * 2**zoom
    return (world_y - tile_y) * TILE_SIZE


def render_tile(
    frame: ConcentrationFrameData,
    zoom: int,
    tile_x: int,
    tile_y: int,
    maximum_value: float,
) -> bytes:
    tile_south, tile_west, tile_north, tile_east = _tile_bounds(zoom, tile_x, tile_y)
    indexes = np.flatnonzero(
        (frame.east > tile_west)
        & (frame.west < tile_east)
        & (frame.north > tile_south)
        & (frame.south < tile_north)
    )
    image = Image.new("RGBA", (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    longitude_span = tile_east - tile_west
    for index in indexes:
        normalized = frame.value[index] / maximum_value if maximum_value > 0 else 0.0
        color = _interpolate(COLOR_STOPS, normalized)
        alpha = round(255 * _interpolate(ALPHA_STOPS, frame.confidence[index]))
        left = int(np.floor((frame.west[index] - tile_west) / longitude_span * TILE_SIZE))
        right = int(np.ceil((frame.east[index] - tile_west) / longitude_span * TILE_SIZE)) - 1
        top = int(np.floor(_tile_pixel_y(frame.north[index], zoom, tile_y)))
        bottom = int(np.ceil(_tile_pixel_y(frame.south[index], zoom, tile_y))) - 1
        draw.rectangle(
            (
                max(left, 0),
                max(top, 0),
                min(max(right, left), TILE_SIZE - 1),
                min(max(bottom, top), TILE_SIZE - 1),
            ),
            fill=(*color, alpha),
        )
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


@lru_cache(maxsize=256)
def render_stored_tile(
    frame_id: int,
    content_sha256: str,
    zoom: int,
    tile_x: int,
    tile_y: int,
    maximum_value: float,
) -> bytes:
    return render_tile(
        load_frame(frame_id, content_sha256),
        zoom,
        tile_x,
        tile_y,
        maximum_value,
    )


def value_at(frame: ConcentrationFrameData, latitude: float, longitude: float) -> float | None:
    indexes = np.flatnonzero(
        (frame.west <= longitude)
        & (frame.east >= longitude)
        & (frame.south <= latitude)
        & (frame.north >= latitude)
    )
    if not len(indexes):
        return None
    index = indexes[np.argmax(frame.confidence[indexes])]
    return float(frame.value[index])
