from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)


def _register_adaptive_modules() -> None:
    """Register the copied adaptive submodules so pickle can find them under the 'adaptive' namespace."""
    from app.services.adaptive import irt_rasch, tree_models

    adaptive_pkg = type(sys)("adaptive")
    adaptive_pkg.irt_rasch = irt_rasch
    adaptive_pkg.tree_models = tree_models
    sys.modules["adaptive"] = adaptive_pkg
    sys.modules["adaptive.irt_rasch"] = irt_rasch
    sys.modules["adaptive.tree_models"] = tree_models


@dataclass(frozen=True)
class MLRecommendation:
    predicted_p_correct: float
    confidence: float
    method: str  # "xgb", "irt", "rule"


class AdaptiveModelService:
    def __init__(self) -> None:
        self._irt_bundle: dict[str, Any] | None = None
        self._xgb_model: Any | None = None
        self._load_models()

    def _load_models(self) -> None:
        _register_adaptive_modules()

        if settings.irt_model_path.exists():
            try:
                self._irt_bundle = joblib.load(settings.irt_model_path)
                logger.info("IRT model loaded: games=%s", list(self._irt_bundle.keys()) if self._irt_bundle else "none")
            except Exception:
                logger.exception("Failed to load IRT model")
                self._irt_bundle = None

        if settings.xgb_model_path.exists():
            try:
                self._xgb_model = joblib.load(settings.xgb_model_path)
                if hasattr(self._xgb_model, 'game_to_idx'):
                    logger.info("XGBoost model loaded: games=%s", list(self._xgb_model.game_to_idx.keys()))
            except Exception:
                logger.exception("Failed to load XGBoost model")
                self._xgb_model = None

    @property
    def xgb_available(self) -> bool:
        return self._xgb_model is not None

    @property
    def irt_available(self) -> bool:
        return self._irt_bundle is not None

    def _interactions_to_df(self, interactions: list[dict[str, object]]) -> pd.DataFrame:
        rows = []
        for it in interactions:
            rows.append({
                "user_id": str(it.get("user_id", "")),
                "game": str(it.get("game_type", "")),
                "attempt_index": int(it.get("attempt_index", 0)),
                "correct": int(bool(it.get("correct", False))),
                "time_since_skill": float(it.get("time_since_last_same_game", 0) or 0),
                "consecutive_errors_in_row": int(it.get("consecutive_errors", 0)),
                "total_attempted": int(it.get("total_attempted", 0)),
                "skill_opportunities": int(it.get("skill_opportunities", 0)),
                "past_wrong_ratio": 0.0,
                "sum_right": 0,
            })
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df = df.sort_values("attempt_index")
        df["past_wrong_ratio"] = (df.groupby("user_id")["correct"].transform(
            lambda s: s.shift(1).apply(lambda x: 1.0 - (x if not pd.isna(x) else 1.0))
        )).fillna(0.0)
        df["sum_right"] = df.groupby("user_id")["correct"].transform(
            lambda s: s.shift(1).cumsum()
        ).fillna(0.0)
        return df

    def predict_p_correct(self, user_id: str, game: str, recent_interactions: list[dict[str, object]]) -> tuple[float, float]:
        if not self._xgb_model or not recent_interactions:
            return 0.5, 0.3

        df = self._interactions_to_df(recent_interactions)
        if df.empty:
            return 0.5, 0.3

        try:
            probs = self._xgb_model.predict_proba(df)
            predicted = float(probs[-1])
            predicted = max(0.01, min(0.99, predicted))
            confidence = min(0.85, 0.45 + 0.02 * len(recent_interactions))
            return predicted, confidence
        except Exception:
            logger.exception("XGBoost prediction failed")
            return 0.5, 0.3

    def estimate_theta(self, user_id: str, game: str, interactions: list[dict[str, object]]) -> float | None:
        if not self._irt_bundle or game not in self._irt_bundle:
            return None

        rows = []
        for it in interactions:
            rows.append({
                "user_id": str(it.get("user_id", "")),
                "game": str(it.get("game_type", "")),
                "item_id": f"{game}_{str(it.get('difficulty_level', '0'))}",
                "attempt_index": int(it.get("attempt_index", 0)),
                "correct": int(bool(it.get("correct", False))),
            })

        if not rows:
            return None

        df = pd.DataFrame(rows)
        model = self._irt_bundle[game]
        try:
            return model.estimate_theta_online(df[df["game"] == game])
        except Exception:
            logger.exception("IRT theta estimation failed")
            return None

    def get_user_ability_summary(self, user_id: str, interactions_by_game: dict[str, list[dict[str, object]]]) -> dict[str, dict[str, object]]:
        result: dict[str, dict[str, object]] = {}
        for game, interactions in interactions_by_game.items():
            entry: dict[str, object] = {
                "xgb_p_correct": None,
                "xgb_confidence": None,
                "irt_theta": None,
            }
            if self._xgb_model and interactions:
                p, conf = self.predict_p_correct(user_id, game, interactions)
                entry["xgb_p_correct"] = round(p, 4)
                entry["xgb_confidence"] = round(conf, 4)
            if self._irt_bundle and game in self._irt_bundle:
                theta = self.estimate_theta(user_id, game, interactions)
                entry["irt_theta"] = round(theta, 4) if theta is not None else None
            result[game] = entry
        return result


adaptive_model_service = AdaptiveModelService()
