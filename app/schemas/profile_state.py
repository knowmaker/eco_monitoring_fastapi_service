from pydantic import BaseModel


class ProfileLevelPointOut(BaseModel):
    height: float
    temperature: float | None


class ProfileInversionOut(BaseModel):
    power: float | None
    lower: float | None
    upper: float | None
    deltaT: float | None


class ProfileHourOut(BaseModel):
    hour: int
    levels: list[ProfileLevelPointOut]
    inversion: ProfileInversionOut | None = None


class ProfileDayOut(BaseModel):
    day: int
    levels: list[ProfileLevelPointOut]
    inversion: ProfileInversionOut | None = None


class ProfileStateHourlyResponse(BaseModel):
    date: str
    profiles: list[ProfileHourOut]


class ProfileStateMonthlyResponse(BaseModel):
    month: str
    profiles: list[ProfileDayOut]
