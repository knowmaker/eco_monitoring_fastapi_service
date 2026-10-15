from typing import Literal

from pydantic import BaseModel, Field


class PollutantLimitOut(BaseModel):
    pollutant_code: str
    pdk_max_once: float | None
    pdk_daily: float | None
    pdk_annual: float | None
    comparison_pdk: float | None
    comparison_kind: str


class LatestGasSubstanceOut(BaseModel):
    substance_code: str
    value: float | None
    limit: PollutantLimitOut | None = None


class LatestGasOut(BaseModel):
    timestamp_ms: int
    substances: list[LatestGasSubstanceOut]


class LatestDustOut(BaseModel):
    timestamp_ms: int
    pm1: float | None
    pm2: float | None
    pm10: float | None
    tsp: float | None
    limits: dict[str, PollutantLimitOut | None] = Field(default_factory=dict)


class LatestMeteoOut(BaseModel):
    timestamp_ms: int
    atm_press: float | None
    air_temp: float | None
    air_hum: float | None
    hor_win_dir: float | None
    hor_win_spd: float | None


class LatestIvtmOut(BaseModel):
    timestamp_ms: int
    sensor_ivtm_hum: float | None
    sensor_ivtm_temp: float | None


class LatestProfileLevelOut(BaseModel):
    height: float
    temperature: float | None


class LatestProfileOut(BaseModel):
    timestamp_ms: int
    levels: list[LatestProfileLevelOut]
    inversion_power: float | None
    inversion_lower: float | None
    inversion_upper: float | None
    inversion_delta_t: float | None


class StationLatestResponse(BaseModel):
    monitoring_post_id: int
    timestamp_ms: int | None
    time_mode: Literal["exact", "hourly"]
    gas: LatestGasOut | None
    dust: LatestDustOut | None
    meteo: LatestMeteoOut | None
    ivtm: LatestIvtmOut | None
    profile: LatestProfileOut | None = None
