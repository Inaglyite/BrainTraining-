from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.auth import FirstTestUpdateRequest, LoginRequest, RegisterRequest, UserProfileResponse
from app.services.auth_service import get_profile, login_user, register_user, set_first_test_completed

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserProfileResponse, status_code=201)
def register(payload: RegisterRequest) -> UserProfileResponse:
    try:
        return register_user(payload.user_id, payload.password, payload.birthday, payload.role)
    except ValueError as exc:
        if str(exc) == "user_id_already_exists":
            raise HTTPException(status_code=409, detail="User ID already exists") from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=UserProfileResponse)
def login(payload: LoginRequest) -> UserProfileResponse:
    try:
        return login_user(payload.user_id, payload.password)
    except ValueError as exc:
        if str(exc) == "invalid_credentials":
            raise HTTPException(status_code=401, detail="Invalid user ID or password") from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/users/{user_id}", response_model=UserProfileResponse)
def get_user_profile(user_id: str) -> UserProfileResponse:
    try:
        return get_profile(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc


@router.patch("/users/{user_id}/first-test", response_model=UserProfileResponse)
def update_first_test(user_id: str, payload: FirstTestUpdateRequest) -> UserProfileResponse:
    try:
        return set_first_test_completed(user_id, payload.first_test_completed)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc

