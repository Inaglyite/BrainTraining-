from __future__ import annotations

import base64
import logging
import time
from dataclasses import dataclass
from typing import Literal

import joblib
import numpy as np

from app.core.config import settings
from app.schemas.vision import GestureDetectResponse, GestureSet
from app.services.features import build_feature_vector, flatten_landmarks

logger = logging.getLogger(__name__)

# Heavy optional deps — only needed for legacy base64-image endpoint
try:
    import cv2  # noqa: F401
    from app.services.hand_detector import HandDetector  # noqa: F401
    _LEGACY_IMAGE_ENDPOINT_AVAILABLE = True
except ImportError:
    _LEGACY_IMAGE_ENDPOINT_AVAILABLE = False
    logger.info("mediapipe/opencv not installed — legacy /vision/gestures endpoint disabled")



@dataclass
class _ModelBundle:
    model: object
    label_encoder: object
    valid_labels: set[str]


class GestureModelService:
    def __init__(self) -> None:
        self._bundles: dict[GestureSet, _ModelBundle] = {}
        self._detector: HandDetector | None = None

    @staticmethod
    def _model_config(gesture_set: GestureSet) -> tuple[Literal["digits", "rps"], object, set[str]]:
        if gesture_set == "rps":
            return "rps", settings.rps_model_path, {"rock", "paper", "scissors"}
        return "digits", settings.model_path, {str(i) for i in range(1, 10)}

    def _load_bundle(self, gesture_set: GestureSet) -> _ModelBundle:
        bundle = self._bundles.get(gesture_set)
        if bundle is not None:
            return bundle

        _, model_path, valid_labels = self._model_config(gesture_set)
        if not model_path.exists():
            raise FileNotFoundError(f"Gesture model not found: {model_path}")

        payload = joblib.load(model_path)
        model = payload["model"]
        label_encoder = payload["label_encoder"]
        bundle = _ModelBundle(model=model, label_encoder=label_encoder, valid_labels=valid_labels)
        self._bundles[gesture_set] = bundle
        return bundle

    def _get_detector(self) -> HandDetector:
        if not _LEGACY_IMAGE_ENDPOINT_AVAILABLE:
            raise RuntimeError("mediapipe not installed — use /vision/classify instead")
        if self._detector is None:
            self._detector = HandDetector(max_num_hands=1, model_path=settings.task_model_path)
        return self._detector

    @staticmethod
    def _decode_image(image_base64: str) -> np.ndarray:
        raw = image_base64.strip()
        if raw.startswith("data:"):
            raw = raw.split(",", 1)[1]

        try:
            image_bytes = base64.b64decode(raw)
        except Exception as exc:
            raise ValueError("Invalid base64 image payload") from exc
        encoded = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image payload")
        return img

    def predict_from_landmarks(
        self,
        landmarks: list[float],
        threshold: float | None = None,
        gesture_set: GestureSet = "digits",
    ) -> GestureDetectResponse:
        use_threshold = threshold if threshold is not None else settings.default_threshold
        bundle = self._load_bundle(gesture_set)

        if len(landmarks) != 63:
            return GestureDetectResponse(
                gesture="unknown", raw_label=None, confidence=None,
                hand_detected=False, threshold=use_threshold,
            )

        flat = np.array(landmarks, dtype=np.float32)
        feat = build_feature_vector(flat).reshape(1, -1)
        prob = bundle.model.predict_proba(feat)[0]
        idx = int(prob.argmax())
        conf = float(prob[idx])
        pred = str(bundle.label_encoder.inverse_transform([idx])[0])

        if conf < use_threshold or pred not in bundle.valid_labels:
            return GestureDetectResponse(
                gesture="unknown",
                raw_label=pred if pred in bundle.valid_labels else None,
                confidence=conf,
                hand_detected=True,
                threshold=use_threshold,
            )

        return GestureDetectResponse(
            gesture=pred, raw_label=pred, confidence=conf,
            hand_detected=True, threshold=use_threshold,
        )

    def predict_from_base64(
        self,
        image_base64: str,
        threshold: float | None = None,
        gesture_set: GestureSet = "digits",
    ) -> GestureDetectResponse:
        started = time.perf_counter()
        use_threshold = threshold if threshold is not None else settings.default_threshold
        bundle = self._load_bundle(gesture_set)
        detector = self._get_detector()

        frame = self._decode_image(image_base64)
        detection = detector.detect(frame)
        if detection.landmarks is None:
            response = GestureDetectResponse(
                gesture="unknown",
                raw_label=None,
                confidence=None,
                hand_detected=False,
                threshold=use_threshold,
            )
            latency_ms = (time.perf_counter() - started) * 1000.0
            logger.info(
                "gesture_infer set=%s latency_ms=%.2f hand_detected=%s raw_label=%s confidence=%s output=%s",
                gesture_set,
                latency_ms,
                response.hand_detected,
                response.raw_label,
                response.confidence,
                response.gesture,
            )
            return response

        flat = flatten_landmarks(detection.landmarks)
        feat = build_feature_vector(flat).reshape(1, -1)
        prob = bundle.model.predict_proba(feat)[0]
        idx = int(prob.argmax())
        conf = float(prob[idx])
        pred = str(bundle.label_encoder.inverse_transform([idx])[0])
        valid_label = pred in bundle.valid_labels

        if conf < use_threshold or not valid_label:
            response = GestureDetectResponse(
                gesture="unknown",
                raw_label=pred if valid_label else None,
                confidence=conf,
                hand_detected=True,
                threshold=use_threshold,
            )
            latency_ms = (time.perf_counter() - started) * 1000.0
            logger.info(
                "gesture_infer set=%s latency_ms=%.2f hand_detected=%s raw_label=%s confidence=%.4f output=%s",
                gesture_set,
                latency_ms,
                response.hand_detected,
                response.raw_label,
                conf,
                response.gesture,
            )
            return response

        response = GestureDetectResponse(
            gesture=pred,
            raw_label=pred,
            confidence=conf,
            hand_detected=True,
            threshold=use_threshold,
        )
        latency_ms = (time.perf_counter() - started) * 1000.0
        logger.info(
            "gesture_infer set=%s latency_ms=%.2f hand_detected=%s raw_label=%s confidence=%.4f output=%s",
            gesture_set,
            latency_ms,
            response.hand_detected,
            response.raw_label,
            conf,
            response.gesture,
        )
        return response


gesture_model_service = GestureModelService()
