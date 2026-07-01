from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ExpoTokenRegister(BaseModel):
    token: str
    platform: Optional[str] = None  # "ios" | "android"


class UserDeviceResponse(BaseModel):
    id: int
    user_id: int
    expo_push_token: str
    platform: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
