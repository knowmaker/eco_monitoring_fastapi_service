from typing import Literal

from pydantic import BaseModel, Field


PostType = Literal["stationary", "mobile", "drone"]


class MonitoringPostOut(BaseModel):
    id: int
    serial: str
    name: str | None
    post_type: PostType | None
    latitude: float | None
    longitude: float | None
    is_confirmed: bool


class MonitoringPostAdminOut(MonitoringPostOut):
    notes: str | None


class MonitoringPostsResponse(BaseModel):
    monitoring_posts: list[MonitoringPostOut]


class MonitoringPostsAdminResponse(BaseModel):
    monitoring_posts: list[MonitoringPostAdminOut]


class MonitoringPostUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    post_type: PostType | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    notes: str | None = Field(default=None, max_length=5000)
    is_confirmed: bool | None = None
