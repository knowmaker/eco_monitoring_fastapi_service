from pydantic import BaseModel


class DeviceInfo(BaseModel):
    serial: str
    latitude: float | None
    longitude: float | None


class DevicesResponse(BaseModel):
    devices: list[DeviceInfo]
