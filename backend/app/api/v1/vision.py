from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.vision import GestureDetectRequest, GestureDetectResponse, LandmarkClassifyRequest
from app.services.gesture_model_service import gesture_model_service

router = APIRouter(prefix="/vision", tags=["vision"])


@router.post("/gestures", response_model=GestureDetectResponse)
def detect_gesture(payload: GestureDetectRequest) -> GestureDetectResponse:
    try:
        return gesture_model_service.predict_from_base64(
            payload.image_base64,
            payload.min_confidence,
            payload.gesture_set,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/classify", response_model=GestureDetectResponse)
def classify_landmarks(payload: LandmarkClassifyRequest) -> GestureDetectResponse:
    try:
        return gesture_model_service.predict_from_landmarks(
            payload.landmarks,
            payload.min_confidence,
            payload.gesture_set,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Classification failed: {exc}") from exc
