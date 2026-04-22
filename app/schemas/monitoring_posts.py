from pydantic import BaseModel


class MonitoringPostOut(BaseModel):
    id: int
    serial: str
    latitude: float | None
    longitude: float | None
    is_stationary: bool


class MonitoringPostsResponse(BaseModel):
    monitoring_posts: list[MonitoringPostOut]
