from __future__ import annotations

import numpy as np

N_LANDMARKS = 21
N_COORDS = 3


def flatten_landmarks(landmarks: list) -> np.ndarray:
    vec = np.array([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float32)
    return vec.reshape(-1)


def normalize_landmarks(flat_landmarks: np.ndarray) -> np.ndarray:
    if flat_landmarks.size != N_LANDMARKS * N_COORDS:
        raise ValueError("Expected 63 values (21 landmarks x 3 coordinates).")

    pts = flat_landmarks.reshape(N_LANDMARKS, N_COORDS).astype(np.float32)
    wrist = pts[0].copy()
    pts = pts - wrist

    scale = np.max(np.linalg.norm(pts, axis=1))
    if scale > 1e-6:
        pts = pts / scale

    return pts.reshape(-1)


def build_feature_vector(flat_landmarks: np.ndarray) -> np.ndarray:
    return normalize_landmarks(flat_landmarks)

