from pydantic import BaseModel


class DeviceStateAvailableOut(BaseModel):
    device_type: str
    device_name: str | None


class DeviceStateAvailableResponse(BaseModel):
    devices: list[DeviceStateAvailableOut]
