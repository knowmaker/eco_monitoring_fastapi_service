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


class LatestGasHourlyOut(BaseModel):
    bucket_ms: int
    substances: list[LatestGasSubstanceOut]


class LatestDustHourlyOut(BaseModel):
    bucket_ms: int
    pm1: float | None
    pm2: float | None
    pm10: float | None
    tsp: float | None
    limits: dict[str, PollutantLimitOut | None] = Field(default_factory=dict)


class LatestMeteoHourlyOut(BaseModel):
    bucket_ms: int
    atm_press: float | None
    air_temp: float | None
    air_hum: float | None
    hor_win_dir: float | None
    hor_win_spd: float | None


class LatestIvtmHourlyOut(BaseModel):
    bucket_ms: int
    sensor_ivtm_hum: float | None
    sensor_ivtm_temp: float | None


class StationLatestHourlyResponse(BaseModel):
    monitoring_post_id: int
    bucket_ms: int | None
    gas: LatestGasHourlyOut | None
    dust: LatestDustHourlyOut | None
    meteo: LatestMeteoHourlyOut | None
    ivtm: LatestIvtmHourlyOut | None
