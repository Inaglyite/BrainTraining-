from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.request import urlretrieve

import cv2
import mediapipe as mp

DEFAULT_TASK_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)


@dataclass
class DetectionResult:
    landmarks: Optional[list]


class HandDetector:
    """Compatibility wrapper for MediaPipe solutions API and tasks API."""

    def __init__(self, max_num_hands: int = 1, model_path: Path | None = None) -> None:
        self.max_num_hands = max_num_hands
        self._mode = "tasks" if not hasattr(mp, "solutions") else "solutions"
        self._hands = None
        self._landmarker = None

        if self._mode == "solutions":
            self._init_solutions()
        else:
            self._init_tasks(model_path=model_path)

    def _init_solutions(self) -> None:
        solutions = getattr(mp, "solutions", None)
        if solutions is None:
            raise RuntimeError("mediapipe.solutions is unavailable in this environment.")

        mp_hands = solutions.hands
        self._hands = mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=self.max_num_hands,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5,
        )

    def _init_tasks(self, model_path: Path | None = None) -> None:
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        resolved_model = model_path or Path("models/hand_landmarker.task")
        self._ensure_task_model(resolved_model)

        base_options = python.BaseOptions(model_asset_path=str(resolved_model))
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=self.max_num_hands,
            min_hand_detection_confidence=0.6,
            min_tracking_confidence=0.5,
            min_hand_presence_confidence=0.5,
            running_mode=vision.RunningMode.IMAGE,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)

    @staticmethod
    def _ensure_task_model(model_path: Path) -> None:
        if model_path.exists():
            return
        model_path.parent.mkdir(parents=True, exist_ok=True)
        urlretrieve(DEFAULT_TASK_MODEL_URL, model_path)

    def detect(self, bgr_frame) -> DetectionResult:
        if self._mode == "solutions":
            rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            result = self._hands.process(rgb)
            if not result.multi_hand_landmarks:
                return DetectionResult(landmarks=None)
            return DetectionResult(landmarks=result.multi_hand_landmarks[0].landmark)

        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect(mp_image)
        if not result.hand_landmarks:
            return DetectionResult(landmarks=None)
        return DetectionResult(landmarks=result.hand_landmarks[0])

    def close(self) -> None:
        if self._hands is not None:
            self._hands.close()
        if self._landmarker is not None:
            self._landmarker.close()

