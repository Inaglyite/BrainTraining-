import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

os.environ.setdefault("SQLITE_DB_PATH", str(Path(tempfile.gettempdir()) / "yusnxing-test-game-data.db"))

from app.services.gesture_model_service import GestureModelService, _ModelBundle


class _DummyModel:
    def predict_proba(self, _features: np.ndarray) -> np.ndarray:
        return np.array([[0.95]], dtype=np.float32)


class _DummyEncoder:
    def __init__(self, label: str) -> None:
        self._label = label

    def inverse_transform(self, _indices: list[int]) -> list[str]:
        return [self._label]


class GestureModelServiceTest(unittest.TestCase):
    def test_rps_gesture_set_accepts_rps_label(self) -> None:
        service = GestureModelService()
        service._bundles["rps"] = _ModelBundle(
            model=_DummyModel(),
            label_encoder=_DummyEncoder("rock"),
            valid_labels={"rock", "paper", "scissors"},
        )

        landmarks = [SimpleNamespace(x=0.1, y=0.2, z=0.3) for _ in range(21)]
        detector = SimpleNamespace(detect=lambda _frame: SimpleNamespace(landmarks=landmarks))

        with patch.object(service, "_get_detector", return_value=detector), \
             patch.object(service, "_decode_image", return_value=np.zeros((4, 4, 3), dtype=np.uint8)):
            result = service.predict_from_base64("ignored", gesture_set="rps")

        self.assertEqual(result.gesture, "rock")
        self.assertEqual(result.raw_label, "rock")

    def test_digits_gesture_set_rejects_rps_label(self) -> None:
        service = GestureModelService()
        service._bundles["digits"] = _ModelBundle(
            model=_DummyModel(),
            label_encoder=_DummyEncoder("rock"),
            valid_labels={str(i) for i in range(1, 10)},
        )

        landmarks = [SimpleNamespace(x=0.1, y=0.2, z=0.3) for _ in range(21)]
        detector = SimpleNamespace(detect=lambda _frame: SimpleNamespace(landmarks=landmarks))

        with patch.object(service, "_get_detector", return_value=detector), \
             patch.object(service, "_decode_image", return_value=np.zeros((4, 4, 3), dtype=np.uint8)):
            result = service.predict_from_base64("ignored", gesture_set="digits")

        self.assertEqual(result.gesture, "unknown")
        self.assertIsNone(result.raw_label)


if __name__ == "__main__":
    unittest.main()
