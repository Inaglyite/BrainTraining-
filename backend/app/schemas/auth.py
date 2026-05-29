from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RoleName = Literal["student", "worker", "elder"]


class RegisterRequest(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    birthday: str
    role: RoleName


class LoginRequest(BaseModel):
    user_id: str
    password: str


class UserProfileResponse(BaseModel):
    user_id: str
    birthday: str
    role: RoleName
    first_test_completed: bool


class FirstTestUpdateRequest(BaseModel):
    first_test_completed: bool

