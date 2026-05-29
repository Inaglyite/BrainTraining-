from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"

# Load .env before constructing settings
_env_file = BACKEND_ROOT / ".env"
if _env_file.exists():
    load_dotenv(_env_file)


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Brain Training Gesture API")
    app_env: str = os.getenv("APP_ENV", "dev")
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    model_path: Path = Path(
        os.getenv(
            "GESTURE_MODEL_PATH",
            str(PROJECT_ROOT / "src/assets/models/GestureRecognizer/gesture_model.joblib"),
        )
    )
    rps_model_path: Path = Path(
        os.getenv(
            "RPS_GESTURE_MODEL_PATH",
            str(PROJECT_ROOT / "src/assets/models/GestureRecognizer/rps_model.joblib"),
        )
    )
    task_model_path: Path = Path(
        os.getenv(
            "MEDIAPIPE_TASK_MODEL_PATH",
            str(BACKEND_ROOT / "models/hand_landmarker.task"),
        )
    )
    irt_model_path: Path = Path(
        os.getenv(
            "IRT_MODEL_PATH",
            str(PROJECT_ROOT / "src/assets/models/DKTandIRT/irt_per_game.pkl"),
        )
    )
    xgb_model_path: Path = Path(
        os.getenv(
            "XGB_MODEL_PATH",
            str(PROJECT_ROOT / "src/assets/models/DKTandIRT/xgb_seq.pkl"),
        )
    )
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BACKEND_ROOT / 'data' / 'game_data.db'}",
    )
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    sqlite_db_path: Path = Path(
        os.getenv(
            "SQLITE_DB_PATH",
            str(BACKEND_ROOT / "data/game_data.db"),
        )
    )
    default_threshold: float = float(os.getenv("GESTURE_MIN_CONFIDENCE", "0.30"))


settings = Settings()
