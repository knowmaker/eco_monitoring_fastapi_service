from pydantic import BaseModel


class LatestGasSubstanceOut(BaseModel):
    substance_code: str
    value: float | None


class LatestGasHourlyOut(BaseModel):
    substances: list[LatestGasSubstanceOut]


class LatestDustHourlyOut(BaseModel):
    humidity: float | None
    temp: float | None
    pm1: float | None
    pm2: float | None
    pm10: float | None
    tsp: float | None


class LatestMeteoHourlyOut(BaseModel):
    atm_press: float | None
    air_temp: float | None
    air_hum: float | None
    hor_win_dir: float | None
    hor_win_spd: float | None


class LatestIvtmHourlyOut(BaseModel):
    sensor_ivtm_hum: float | None
    sensor_ivtm_temp: float | None


class StationLatestHourlyResponse(BaseModel):
    monitoring_post_id: int
    bucket_ms: int | None
    gas: LatestGasHourlyOut | None
    dust: LatestDustHourlyOut | None
    meteo: LatestMeteoHourlyOut | None
    ivtm: LatestIvtmHourlyOut | None
