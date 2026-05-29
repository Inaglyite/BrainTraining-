from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import median
from typing import Any

import joblib

from app.core.config import settings
from app.schemas.vision import GameName


@dataclass(frozen=True)
class DifficultyRange:
    min_value: float
    max_value: float
    step: float
    ladder: tuple[float, ...] | None = None


@dataclass(frozen=True)
class DifficultyRecommendation:
    user_id: str
    game_type: str
    current_difficulty: float
    recommended_difficulty: float
    action: str
    target_band: tuple[float, float]
    predicted_p_correct: float
    confidence: float
    reason_codes: list[str]
    explanation_cn: str


_GAME_CN: dict[GameName, str] = {
    "suan-shi": "算式回溯",
    "shu-xiang": "数箱子",
    "rps": "指令石头剪刀布",
}


def _build_suanshi_ladder() -> tuple[float, ...]:
    ladder: list[float] = []
    for n in range(2, 8):
        ladder.append(float(f"{n}.0"))
        ladder.append(float(f"{n}.5"))
        ladder.append(float(f"{n}.7"))
    return tuple(ladder)


_RANGES: dict[GameName, DifficultyRange] = {
    "shu-xiang": DifficultyRange(min_value=1.0, max_value=10.0, step=1.0),
    "suan-shi": DifficultyRange(min_value=2.0, max_value=7.7, step=0.1, ladder=_build_suanshi_ladder()),
    "rps": DifficultyRange(min_value=1.0, max_value=3.0, step=1.0, ladder=(1.0, 2.0, 3.0)),
}


class DifficultyService:
    def __init__(self) -> None:
        self._irt_bundle: Any | None = None
        self._load_irt_bundle()

    def _load_irt_bundle(self) -> None:
        try:
            if settings.irt_model_path.exists():
                self._irt_bundle = joblib.load(settings.irt_model_path)
        except Exception:
            self._irt_bundle = None

    @staticmethod
    def _ml_predict(user_id: str, game: str, recent_interactions: list[dict[str, object]]) -> tuple[float, float] | None:
        try:
            from app.services.adaptive_service import adaptive_model_service
            if adaptive_model_service.xgb_available:
                return adaptive_model_service.predict_p_correct(user_id, game, recent_interactions)
        except Exception:
            pass
        return None

    @staticmethod
    def _clamp(x: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, x))

    @staticmethod
    def _logit(p: float) -> float:
        eps = 1e-6
        p = max(eps, min(1.0 - eps, p))
        return math.log(p / (1.0 - p))

    def _normalize_difficulty(self, game: GameName, value: float) -> float:
        cfg = _RANGES[game]
        if cfg.ladder:
            nearest = min(cfg.ladder, key=lambda v: abs(v - value))
            return float(nearest)

        steps = round((value - cfg.min_value) / cfg.step)
        normalized = cfg.min_value + steps * cfg.step
        return round(self._clamp(normalized, cfg.min_value, cfg.max_value), 2)

    def _difficulty_steps(self, game: GameName, current: float, delta: int) -> float:
        cfg = _RANGES[game]
        if delta == 0:
            return self._normalize_difficulty(game, current)

        if cfg.ladder:
            ladder = cfg.ladder
            current_norm = self._normalize_difficulty(game, current)
            idx = ladder.index(current_norm)
            nxt = self._clamp(idx + delta, 0, len(ladder) - 1)
            return float(ladder[int(nxt)])

        moved = current + (cfg.step * delta)
        return self._normalize_difficulty(game, moved)

    @staticmethod
    def _extract_speed_bucket(difficulty: float) -> str:
        decimal = round(difficulty - math.floor(difficulty), 1)
        if abs(decimal - 0.7) < 0.11:
            return "fast"
        if abs(decimal - 0.5) < 0.11:
            return "normal"
        return "slow"

    def _response_time_slow_and_error_rising(
        self,
        recent_interactions: list[dict[str, object]],
        current_response_time: float,
        current_correct: bool,
    ) -> bool:
        if len(recent_interactions) < 4:
            return False

        recent_rts = [float(it["response_time"]) for it in recent_interactions[:4] if it.get("response_time") is not None]
        baseline_rts = [float(it["response_time"]) for it in recent_interactions[4:12] if it.get("response_time") is not None]
        if not recent_rts or not baseline_rts:
            return False

        recent_wrong = sum(1 for it in recent_interactions[:4] if not bool(it["correct"]))
        baseline_wrong = sum(1 for it in recent_interactions[4:12] if not bool(it["correct"]))

        rt_slower = median(recent_rts) > median(baseline_rts) * 1.3
        wrong_rising = recent_wrong > baseline_wrong
        return rt_slower and wrong_rising and (not current_correct) and current_response_time > 0

    def _estimate_predicted_p(
        self,
        game: GameName,
        current_difficulty: float,
        recent_interactions: list[dict[str, object]],
    ) -> tuple[float, float]:
        # Try ML model first (XGBoost)
        if recent_interactions:
            user_id = str(recent_interactions[0].get("user_id", ""))
            ml_result = self._ml_predict(user_id, game, recent_interactions)
            if ml_result is not None:
                return ml_result

        # Fallback to rule-based approximation
        if recent_interactions:
            sample = recent_interactions[:20]
            acc = sum(1 for it in sample if bool(it["correct"])) / len(sample)
        else:
            acc = 0.7

        theta_est = self._logit(acc)
        cfg = _RANGES[game]
        norm = (current_difficulty - cfg.min_value) / (cfg.max_value - cfg.min_value + 1e-9)
        item_b = -2.0 + 4.0 * norm

        p = 1.0 / (1.0 + math.exp(-(theta_est - item_b)))
        p = float(self._clamp(p, 0.01, 0.99))

        confidence = 0.55
        if len(recent_interactions) >= 12:
            confidence = 0.8
        elif len(recent_interactions) >= 6:
            confidence = 0.68

        if isinstance(self._irt_bundle, dict) and game in self._irt_bundle:
            confidence = min(0.9, confidence + 0.05)

        return p, confidence

    def recommend_next_difficulty(
        self,
        user_id: str,
        game: GameName,
        current_difficulty: float,
        current_correct: bool,
        current_response_time: float,
        consecutive_errors: int,
        recent_interactions: list[dict[str, object]],
    ) -> DifficultyRecommendation:
        current = self._normalize_difficulty(game, current_difficulty)
        predicted_p, confidence = self._estimate_predicted_p(game, current, recent_interactions)

        reason_codes: list[str] = []
        action = "keep"
        steps = 0

        if predicted_p < 0.65:
            action = "decrease"
            steps = 1
            reason_codes.append("theta_low")
        elif predicted_p > 0.85:
            action = "increase"
            steps = 1
            reason_codes.append("theta_high")
        elif 0.65 <= predicted_p <= 0.75:
            action = "keep"
            steps = 0
            reason_codes.append("in_band")

        slow_response = self._response_time_slow_and_error_rising(
            recent_interactions,
            current_response_time,
            current_correct,
        )

        if consecutive_errors >= 2:
            reason_codes.append("consecutive_errors")
            if action == "decrease":
                steps += 1
            else:
                action = "decrease"
                steps = 1

        if slow_response:
            reason_codes.append("slow_response")
            action = "decrease"
            steps = max(steps, 1)

        # Conservative fallback with weak evidence: only one notch per adjustment.
        if len(recent_interactions) < 6 and consecutive_errors < 2 and not slow_response:
            steps = min(steps, 1)

        steps = min(steps, 2)

        recommended = current
        if action == "increase":
            recommended = self._difficulty_steps(game, current, steps)
        elif action == "decrease":
            if game == "suan-shi" and slow_response:
                # Prefer speed reduction before reducing n-back complexity.
                bucket = self._extract_speed_bucket(current)
                if bucket == "fast":
                    recommended = self._normalize_difficulty(game, math.floor(current) + 0.5)
                elif bucket == "normal":
                    recommended = self._normalize_difficulty(game, math.floor(current) + 0.0)
                else:
                    recommended = self._difficulty_steps(game, current, -steps)
            else:
                recommended = self._difficulty_steps(game, current, -steps)

        if recommended > current:
            action = "increase"
        elif recommended < current:
            action = "decrease"
        else:
            action = "keep"

        if not reason_codes and action == "keep":
            reason_codes.append("in_band")

        explanation = (
            f"预测正确率为{predicted_p:.2f}，根据近期表现建议{('提高' if action == 'increase' else '降低' if action == 'decrease' else '保持')}到{recommended:.1f}。"
        )

        return DifficultyRecommendation(
            user_id=user_id,
            game_type=_GAME_CN[game],
            current_difficulty=current,
            recommended_difficulty=recommended,
            action=action,
            target_band=(0.65, 0.75),
            predicted_p_correct=predicted_p,
            confidence=round(self._clamp(confidence, 0.0, 1.0), 2),
            reason_codes=reason_codes,
            explanation_cn=explanation,
        )

    def get_default_difficulty(self, game: GameName) -> float:
        cfg = _RANGES[game]
        if cfg.ladder:
            return float(cfg.ladder[0])
        return cfg.min_value

    def normalize_for_game(self, game: GameName, difficulty: float) -> float:
        return self._normalize_difficulty(game, difficulty)

    def get_answer_time_limit_ms(self, game: GameName, difficulty: float) -> int:
        d = self._normalize_difficulty(game, difficulty)
        if game == "rps":
            if d <= 1.0:
                return 3000
            if d <= 2.0:
                return 2200
            return 1500

        if game == "shu-xiang":
            # Higher difficulty means faster rounds.
            return int(max(1300, 3600 - (d - 1.0) * 250))

        # suan-shi: n.0 slow, n.5 normal, n.7 fast
        speed = self._extract_speed_bucket(d)
        if speed == "fast":
            return 1800
        if speed == "normal":
            return 2500
        return 3200


difficulty_service = DifficultyService()
